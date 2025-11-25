import pandas as pd
import numpy as np
import os

# 1. Setup Directories
output_dir = 'data/clean'
os.makedirs(output_dir, exist_ok=True)

# 2. Define Time Range
years = np.arange(2025, 2051)
df = pd.DataFrame({'Year': years})

# 3. Interpolation Function
def get_linear_trend(start_val, end_val, year_arr):
    return np.interp(year_arr, [2025, 2050], [start_val, end_val])

# 4. Generate Base Prices (Points 1 & 2)
# Jet A-1: $800 -> $950
df['Price_JetA1_USD'] = get_linear_trend(800, 950, years)

# HEFA (Bio-SAF): $2,200 -> $1,850
df['Price_HEFA_USD'] = get_linear_trend(2200, 1850, years)

# PtL (e-Fuels): $3,800 -> $1,200
df['Price_PtL_USD'] = get_linear_trend(3800, 1200, years)

# Carbon Price (EU ETS in EUR): 90 -> 275
carbon_eur = get_linear_trend(90, 275, years)
df['Carbon_Price_EU_ETS_EUR'] = carbon_eur

# Exchange Rate & Conversion
exchange_rate = 1.10
df['Exchange_Rate_USD_EUR'] = exchange_rate
df['Carbon_Price_USD'] = df['Carbon_Price_EU_ETS_EUR'] * exchange_rate

# 5. Generate Constants / Hadi's Penalties (Point 3)
# Logistics Penalty (Cost of trucking in S1)
df['Logistics_Penalty_USD_per_Tonne'] = 150.0

# Logistics Carbon Penalty (Emissions of trucking in S1)
df['Logistics_Emissions_gCO2_per_tkm'] = 50.0

# HEFA Supply Cap (The "Feedstock Wall")
df['HEFA_EU_Supply_Cap_Mt'] = 5.0

# 6. Formatting & Save
# Round prices to 2 decimals
numeric_cols = df.columns.drop('Year')
df[numeric_cols] = df[numeric_cols].round(2)

output_path = os.path.join(output_dir, 'layer3_economic_assumptions.csv')
df.to_csv(output_path, index=False)

# 7. Verification Output
print(f"✅ Success! Economic Data Generated at: {output_path}")
print("\n--- Preview: First 3 Years ---")
print(df.head(3).to_string())
print("\n--- Preview: Last 3 Years ---")
print(df.tail(3).to_string())

