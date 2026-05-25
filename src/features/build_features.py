from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.config import load_yaml_config
from src.utils.paths import ensure_parent, resolve_project_path


def dataset_feature_path(dataset_config_path: str | Path) -> Path:
    dataset_config = load_yaml_config(resolve_project_path(dataset_config_path))
    return resolve_project_path(dataset_config["artifacts"]["feature_path"])


def add_lags(frame: pd.DataFrame, columns: list[str], lags: list[int]) -> pd.DataFrame:
    features = frame.copy()
    for column in columns:
        for lag in lags:
            features[f"{column}_lag_{lag}h"] = features[column].shift(lag)
    return features


def add_target(frame: pd.DataFrame, target_column: str, horizon_hours: int) -> pd.DataFrame:
    features = frame.copy()
    features[f"{target_column}_target_{horizon_hours}h"] = features[target_column].shift(
        -horizon_hours
    )
    return features


def add_load_differences(frame: pd.DataFrame, differences: list[str]) -> pd.DataFrame:
    features = frame.copy()
    pattern = re.compile(r"^load_lag_(\d+)h_minus_load_lag_(\d+)h$")

    for difference in differences:
        match = pattern.match(difference)
        if not match:
            raise ValueError(f"Unsupported load difference feature: {difference}")
        left_lag, right_lag = match.groups()
        left = f"load_mw_lag_{left_lag}h"
        right = f"load_mw_lag_{right_lag}h"
        features[difference] = features[left] - features[right]

    return features


def add_weather_changes(frame: pd.DataFrame, changes: list[str]) -> pd.DataFrame:
    features = frame.copy()
    pattern = re.compile(r"^(.+)_lag_(\d+)h_minus_(.+)_lag_(\d+)h$")

    for change in changes:
        match = pattern.match(change)
        if not match:
            raise ValueError(f"Unsupported weather change feature: {change}")
        left_base, left_lag, right_base, right_lag = match.groups()
        if left_base != right_base:
            raise ValueError(f"Weather change must compare one variable: {change}")

        left = f"{left_base}_lag_{left_lag}h"
        right = f"{right_base}_lag_{right_lag}h"
        features[change] = features[left] - features[right]

    return features


def add_missing_flags(frame: pd.DataFrame, candidate_columns: list[str]) -> pd.DataFrame:
    features = frame.copy()
    for column in candidate_columns:
        if column in features:
            features[f"{column}_is_missing"] = features[column].isna()
    return features


def configured_feature_columns(config: dict) -> list[str]:
    load_config = config["inputs"]["load"]
    weather_config = config["inputs"]["weather"]
    calendar_config = config["inputs"]["calendar"]
    engineered_config = config.get("engineered_features", {})

    feature_columns: list[str] = []
    feature_columns.extend(calendar_config.get("include", []))

    for lag in load_config.get("lags_hours", []):
        feature_columns.append(f"{load_config['value_column']}_lag_{lag}h")

    for variable in weather_config.get("variables", []):
        for lag in weather_config.get("lags_hours", []):
            feature_columns.append(f"{variable}_lag_{lag}h")

    feature_columns.extend(engineered_config.get("degree_days", {}).get("include", []))
    feature_columns.extend(engineered_config.get("load_differences", {}).get("include", []))
    feature_columns.extend(engineered_config.get("weather_changes", {}).get("include", []))

    return feature_columns


def build_features_from_config(config_path: Path) -> pd.DataFrame:
    config = load_yaml_config(config_path)
    target_config = config["target"]
    load_config = config["inputs"]["load"]
    weather_config = config["inputs"]["weather"]
    engineered_config = config.get("engineered_features", {})

    source_path = dataset_feature_path(config["scope"]["dataset_config"])
    output_path = resolve_project_path(config["artifacts"]["output_path"])

    features = pd.read_parquet(source_path).sort_values(target_config["timestamp_column"])
    features[target_config["timestamp_column"]] = pd.to_datetime(
        features[target_config["timestamp_column"]],
        utc=True,
    )

    target_column = target_config["name"]
    target_output_column = f"{target_column}_target_{target_config['horizon_hours']}h"

    features = add_target(features, target_column, int(target_config["horizon_hours"]))
    features = add_lags(
        features,
        [load_config["value_column"]],
        [int(lag) for lag in load_config.get("lags_hours", [])],
    )
    features = add_lags(
        features,
        weather_config.get("variables", []),
        [int(lag) for lag in weather_config.get("lags_hours", [])],
    )

    degree_day_config = engineered_config.get("degree_days", {})
    if degree_day_config.get("include") and "temperature_2m_f" in features:
        base_temperature_f = float(degree_day_config["base_temperature_f"])
        if "cooling_degree_f" in degree_day_config["include"]:
            features["cooling_degree_f"] = np.maximum(
                features["temperature_2m_f"] - base_temperature_f,
                0.0,
            )
        if "heating_degree_f" in degree_day_config["include"]:
            features["heating_degree_f"] = np.maximum(
                base_temperature_f - features["temperature_2m_f"],
                0.0,
            )

    features = add_load_differences(
        features,
        engineered_config.get("load_differences", {}).get("include", []),
    )
    features = add_weather_changes(
        features,
        engineered_config.get("weather_changes", {}).get("include", []),
    )

    missing_flag_candidates = [load_config["value_column"], *weather_config.get("variables", [])]
    features = add_missing_flags(features, missing_flag_candidates)

    feature_columns = configured_feature_columns(config)
    missing_flag_columns = [f"{column}_is_missing" for column in missing_flag_candidates]
    metadata_columns = [
        target_config["timestamp_column"],
        target_column,
        target_output_column,
        load_config.get("missing_flag_column"),
    ]
    output_columns = [
        column
        for column in [*metadata_columns, *feature_columns, *missing_flag_columns]
        if column and column in features.columns
    ]

    modeling_features = features[output_columns].copy()
    required_model_columns = [
        column
        for column in [target_output_column, *feature_columns]
        if column in modeling_features.columns
    ]
    modeling_features = modeling_features.dropna(subset=required_model_columns)

    ensure_parent(output_path)
    modeling_features.to_parquet(output_path, index=False)
    return modeling_features


def summarize_features(features: pd.DataFrame) -> pd.Series:
    start_utc = features["timestamp_utc"].min() if len(features) else pd.NaT
    end_utc = features["timestamp_utc"].max() if len(features) else pd.NaT

    return pd.Series(
        {
            "start_utc": start_utc,
            "end_utc": end_utc,
            "rows": len(features),
            "columns": len(features.columns),
            "null_cells": features.isna().sum().sum(),
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build configured modeling features.")
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    features = build_features_from_config(args.config)
    print(summarize_features(features).to_string())


if __name__ == "__main__":
    main()
