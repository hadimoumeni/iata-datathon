# Jet Fuel Baseline (EU27, 1990-Latest)

- **Dataset**: `jet_fuel_baseline__eu27__annual__1990-LATEST_mt.csv`

- **Method**: Generated via `etl/convert_energy_to_tonnes.py` from Eurostat `nrg_bal_c`. Filters EU27 aviation (domestic + international), kerosene jet fuel, converts ktoe → Mt.

- **Use case**: Anchor for Objective 1 total fuel computations (2025 baseline ~38-39 Mt).

- **Note**: Latest year typically 2023. Conversion factors in `references/assumptions.yaml`.

