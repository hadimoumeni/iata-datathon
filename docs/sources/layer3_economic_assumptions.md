# Economic Assumptions Layer 3 (2025-2050)

- **Dataset**: `layer3_economic_assumptions.csv`

- **Method**: Generated via `etl/generate_economic_data.py` using linear interpolation (2025-2050): Jet A-1 ($800→$950), HEFA ($2,200→$1,850), PtL ($3,800→$1,200), EU ETS (€90→€275). Exchange rate 1.10 USD/EUR. Constants: logistics penalty $150/t, emissions 50 gCO2/t-km, HEFA cap 5.0 Mt.

- **Use case**: Input for Objective 2 Economic Analysis.

- **Note**: Includes $150/t logistics penalty and 5.0 Mt HEFA supply cap. Prices in USD (Real 2024).

