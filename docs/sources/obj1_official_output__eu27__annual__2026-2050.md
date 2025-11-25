# Objective 1 Official Output (EU27, 2026-2050)

- **Dataset**: `obj1_official_output__eu27__annual__2026-2050.csv`

- **Method**: Generated via `etl/compute_obj1.py` combining traffic, SAF blend targets, and fuel baseline. Calibrates 2025 to ~38.5 Mt, scales traffic index to Mt, computes CO2 using EF 3.16 tCO2/t and SAF LCA reduction 75%.

- **Use case**: Official judge-required output for Objective 1 (S0/S1 scenarios, 2026-2050).

- **Note**: Baseline ~38-39 Mt. Schema: Year, Scenario (0=S0, 1=S1), Total_Fuel, SAF_Share, CO2_Emissions, Avoided_CO2. Assumptions in `references/assumptions.yaml`.

