# Feature Pipelines

Feature scripts are config-driven and produce modeling-ready tables from joined data artifacts.

Build the initial minimal PJM load/weather feature table:

```bash
python -m src.features.build_features --config configs/features/pjm_load_weather_minimal.yaml
```

Feature configs define target horizon, allowed predictors, missingness policy, and engineered features. They are candidate research designs and must be evaluated with walk-forward validation before promotion.

The current one-week ERA5 sample is too short for the minimal config's `168h` load lag plus `1h` target horizon, so strict modeling output may contain zero rows until a longer weather window is built. That is expected and should be treated as a data-window adequacy check, not a model result.
