# Dataset Exploration Notebooks

Initial notebooks for the first demand/weather dataset stack:

- `eia930_pjm_load_eda.ipynb`: pulls or loads EIA-930 hourly PJM demand, performs timestamp and continuity checks, and inspects persistence/seasonal-naive errors.
- `era5_hourly_weather_exploration.ipynb`: pulls or loads a small default ERA5 hourly single-level weather sample over an approximate PJM bounding box, then creates first area-average weather features.
- `join_load_weather_pjm.ipynb`: joins PJM load and ERA5 weather by UTC timestamp, creates exploratory calendar/weather features, and sketches a temporal split.
- `feature_load_relationship_diagnostics.ipynb`: ranks same-hour and lagged feature/load relationships, with leakage warnings and simple baseline checks.

Credentials and local setup:

- Set `EIA_API_KEY` before running the EIA notebook.
- Configure Copernicus CDS credentials, usually through `~/.cdsapirc`, before enabling the ERA5 download call.
- The ERA5 notebook defaults to a one-week January 2023 request and keeps `RUN_ERA5_DOWNLOAD = False`. Increase the date range only after validating the pipeline and storage footprint.
- Recommended Python packages: `pandas`, `requests`, `matplotlib`, `pyarrow`, `xarray`, `netcdf4`, and `cdsapi`.

Data lineage:

- Raw EIA data is expected under `data/raw/eia930/`.
- Raw ERA5 NetCDF files are expected under `data/raw/era5/`.
- Derived interim files are written under `data/interim/`.
- Joined feature files are written under `data/features/`.

Evaluation note: these notebooks are for exploration and dataset validation. Forecasting experiments should add horizon-specific feature generation, walk-forward validation, baseline comparison, calibration metrics, and regime-stratified evaluation before drawing model conclusions.
