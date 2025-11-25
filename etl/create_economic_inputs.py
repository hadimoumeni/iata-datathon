"""
Create economic inputs DataFrame for Obj2 (2025-2050).

This script generates a comprehensive economic inputs dataset with:
- Linear interpolations for fuel prices (Jet A-1, HEFA, PtL)
- EU ETS carbon price trajectory
- Currency conversion (USD/EUR)
- Scenario 2 constants (logistics, supply caps)
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ---- Output path ------------------------------------------------------------
OUT_CSV = Path("data/clean/economic_inputs__eu27__annual__2025-2050.csv")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# ---- Year range -------------------------------------------------------------
years = np.arange(2025, 2051)  # 2025 to 2050 inclusive
df = pd.DataFrame({'year': years})

# ---- Linear interpolation parameters ----------------------------------------
# Format: (start_year, start_value, end_year, end_value)
interpolations = {
    'Jet_A1_Price_USD_per_t': (2025, 800.0, 2050, 950.0),
    'HEFA_Price_USD_per_t': (2025, 2200.0, 2050, 1850.0),
    'PtL_Price_USD_per_t': (2025, 3800.0, 2050, 1200.0),
    'Carbon_Price_EUR_per_tCO2': (2025, 90.0, 2050, 275.0),
}

# Apply linear interpolation for each variable
for col_name, (start_year, start_val, end_year, end_val) in interpolations.items():
    # Linear interpolation: value = start_val + (end_val - start_val) * (year - start_year) / (end_year - start_year)
    df[col_name] = start_val + (end_val - start_val) * (df['year'] - start_year) / (end_year - start_year)

# ---- Currency conversion ----------------------------------------------------
EXCHANGE_RATE_USD_EUR = 1.10  # Constant exchange rate
df['Exchange_Rate_USD_EUR'] = EXCHANGE_RATE_USD_EUR
df['Carbon_Price_USD_per_tCO2'] = df['Carbon_Price_EUR_per_tCO2'] * EXCHANGE_RATE_USD_EUR

# ---- Scenario 2 constants (apply to all years) -----------------------------
SCENARIO2_CONSTANTS = {
    'Logistics_Penalty_USD_per_t': 150.0,
    'Logistics_Emissions_Factor_gCO2_per_tkm': 50.0,
    'HEFA_EU_Supply_Cap_Mt': 5.0,
}

for col_name, constant_value in SCENARIO2_CONSTANTS.items():
    df[col_name] = constant_value

# ---- Round to reasonable precision ------------------------------------------
# Prices: 1 decimal place
price_cols = [col for col in df.columns if 'Price' in col or 'Penalty' in col]
for col in price_cols:
    df[col] = df[col].round(1)

# Other numeric columns: 2 decimal places
other_numeric = [col for col in df.columns if col not in ['year'] + price_cols]
for col in other_numeric:
    df[col] = df[col].round(2)

# ---- Reorder columns for readability ----------------------------------------
column_order = [
    'year',
    'Jet_A1_Price_USD_per_t',
    'HEFA_Price_USD_per_t',
    'PtL_Price_USD_per_t',
    'Carbon_Price_EUR_per_tCO2',
    'Exchange_Rate_USD_EUR',
    'Carbon_Price_USD_per_tCO2',
    'Logistics_Penalty_USD_per_t',
    'Logistics_Emissions_Factor_gCO2_per_tkm',
    'HEFA_EU_Supply_Cap_Mt',
]
df = df[column_order]

# ---- Save to CSV ------------------------------------------------------------
df.to_csv(OUT_CSV, index=False)

# ---- Print summary ----------------------------------------------------------
print("=" * 70)
print("ECONOMIC INPUTS DATAFRAME CREATED")
print("=" * 70)
print(f"\nFile: {OUT_CSV}")
print(f"Years: {df['year'].min()} to {df['year'].max()} ({len(df)} years)")
print(f"\nColumns ({len(df.columns)}):")
for i, col in enumerate(df.columns, 1):
    print(f"  {i:2d}. {col}")

print("\n" + "=" * 70)
print("FIRST 5 ROWS:")
print("=" * 70)
print(df.head().to_string(index=False))

print("\n" + "=" * 70)
print("LAST 5 ROWS:")
print("=" * 70)
print(df.tail().to_string(index=False))

print("\n" + "=" * 70)
print("INTERPOLATION ANCHORS (start/end):")
print("=" * 70)
for col in ['Jet_A1_Price_USD_per_t', 'HEFA_Price_USD_per_t', 'PtL_Price_USD_per_t', 'Carbon_Price_EUR_per_tCO2']:
    start_val = df.loc[df['year'] == 2025, col].values[0]
    end_val = df.loc[df['year'] == 2050, col].values[0]
    print(f"  {col:35s}: {start_val:8.1f} (2025) → {end_val:8.1f} (2050)")

print("\n" + "=" * 70)
print("SCENARIO 2 CONSTANTS (all years):")
print("=" * 70)
for col in ['Logistics_Penalty_USD_per_t', 'Logistics_Emissions_Factor_gCO2_per_tkm', 'HEFA_EU_Supply_Cap_Mt']:
    val = df[col].iloc[0]  # All rows have same value
    print(f"  {col:35s}: {val}")

print("\n" + "=" * 70)
print("CURRENCY CONVERSION:")
print("=" * 70)
print(f"  Exchange_Rate_USD_EUR: {EXCHANGE_RATE_USD_EUR} (constant)")
print(f"  Carbon_Price_USD (2025): {df.loc[df['year'] == 2025, 'Carbon_Price_USD_per_tCO2'].values[0]:.1f}")
print(f"  Carbon_Price_USD (2050): {df.loc[df['year'] == 2050, 'Carbon_Price_USD_per_tCO2'].values[0]:.1f}")

