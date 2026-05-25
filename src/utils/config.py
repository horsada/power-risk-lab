from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml_config(path: Path) -> dict[str, Any]:
    with path.open() as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(f"Config must parse to a mapping: {path}")
    return config
