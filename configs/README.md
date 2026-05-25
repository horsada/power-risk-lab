# Configs

Configuration files capture research assumptions that should not live only in notebooks.

- `features/pjm_load_weather_minimal.yaml`: candidate feature recipe for initial PJM EIA-930 plus ERA5 hourly load forecasting experiments. It defines the target horizon, allowed feature groups, missingness policy, baseline expectations, and evaluation guardrails.
- `data/sources/eia930_pjm_2023.yaml`: source-level config for PJM EIA-930 hourly load.
- `data/sources/era5_pjm_box_2023_0101_0107.yaml`: source-level config for the initial ERA5 PJM-box weather sample.
- `data/datasets/pjm_load_era5_sample.yaml`: dataset-level config composing load and weather sources for exploratory analysis.

Feature configs are candidate research designs, not proof that a feature set is valid. Promotion requires walk-forward evaluation, baseline comparison, calibration checks for probabilistic models, and regime-stratified diagnostics.
