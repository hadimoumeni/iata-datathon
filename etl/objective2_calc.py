import pandas as pd
import numpy as np
import os

def calculate_economics():
    # --- 1. SETUP PATHS ---
    # Adjust these filenames if your actual Obj-1 output has a slightly different name
    obj1_path = 'data/metrics/obj1_official_output__eu27__annual__2026-2050.csv' 
    economics_path = 'data/clean/layer3_economic_assumptions.csv'
    output_path = 'data/metrics/obj2_economic_results.csv'
    
    # Check if files exist
    if not os.path.exists(obj1_path):
        print(f"❌ Error: Could not find Objective 1 data at {obj1_path}")
        print("   Please ensure your 'Total_Fuel' and 'SAF_Share' data is ready.")
        return
    
    if not os.path.exists(economics_path):
        print(f"❌ Error: Could not find Economic data at {economics_path}")
        return
    
    # --- 2. LOAD DATA ---
    print("🔄 Loading datasets...")
    df_vol = pd.read_csv(obj1_path) # Volume data (Fuel, Emissions)
    df_price = pd.read_csv(economics_path) # Price data (Jet A1, Carbon, SAF)
    
    # Pivot Obj1 data to separate S0 and S1 scenarios
    # Obj1 has: Year, Scenario (0/1), Total_Fuel, SAF_Share (%), CO2_Emissions, Avoided_CO2
    df_s0 = df_vol[df_vol['Scenario'] == 0].copy()
    df_s1 = df_vol[df_vol['Scenario'] == 1].copy()
    
    # Rename columns for S0
    df_s0 = df_s0.rename(columns={
        'Total_Fuel': 'S0_Total_Fuel_Mt',
        'SAF_Share': 'S0_SAF_Share_Pct',
        'CO2_Emissions': 'S0_CO2_Emissions_Mt',
        'Avoided_CO2': 'S0_Avoided_CO2_Mt'
    })
    
    # Rename columns for S1
    df_s1 = df_s1.rename(columns={
        'Total_Fuel': 'S1_Total_Fuel_Mt',
        'SAF_Share': 'S1_SAF_Share_Pct',
        'CO2_Emissions': 'S1_CO2_Emissions_Mt',
        'Avoided_CO2': 'S1_Avoided_CO2_Mt'
    })
    
    # Merge S0 and S1 on Year
    df_scenarios = pd.merge(df_s0[['Year', 'S0_Total_Fuel_Mt', 'S0_SAF_Share_Pct', 'S0_CO2_Emissions_Mt']],
                           df_s1[['Year', 'S1_Total_Fuel_Mt', 'S1_SAF_Share_Pct', 'S1_CO2_Emissions_Mt']],
                           on='Year', how='inner')
    
    # Merge with price data on Year (Inner join to keep matching years only)
    df = pd.merge(df_scenarios, df_price, on='Year', how='inner')
    
    # --- 3. DEFINE CONSTANTS (Phasing out Free Allowances) ---
    # EU ETS Rule: 50% free in 2025, 0% free from 2026 onwards.
    # We create a 'Paying_Ratio' column: 0.5 in 2025, 1.0 in 2026+
    df['ETS_Paying_Ratio'] = np.where(df['Year'] == 2025, 0.5, 1.0)
    
    # --- 4. SCENARIO 0 (Business as Usual) CALCULATIONS ---
    # Cost = Fuel + Carbon Tax
    
    # S0 Fuel Bill (Assuming 100% Jet A-1 for simplicity in S0, or use S0_SAF_Share if valid)
    # Note: If S0 has small SAF uptake (e.g. 1%), we should account for it, but usually S0 ~ Baseline price.
    # We will use the Price_JetA1_USD for the entire S0 volume to represent "Minimal Action"
    df['S0_Fuel_Cost_Bn'] = (df['S0_Total_Fuel_Mt'] * df['Price_JetA1_USD']) / 1000 # /1000 for Billions
    
    # S0 Carbon Bill (Paying for emissions based on ETS ratio)
    df['S0_Carbon_Cost_Bn'] = (df['S0_CO2_Emissions_Mt'] * df['ETS_Paying_Ratio'] * df['Carbon_Price_USD']) / 1000
    
    df['S0_Total_Cost_Bn'] = df['S0_Fuel_Cost_Bn'] + df['S0_Carbon_Cost_Bn']
    
    # --- 5. SCENARIO 1 (Policy Mandate) CALCULATIONS ---
    # This is where the "Feedstock Wall" logic applies.
    
    # A. Calculate Volumes (SAF_Share is in percentage, convert to fraction)
    df['S1_SAF_Vol_Mt'] = df['S1_Total_Fuel_Mt'] * (df['S1_SAF_Share_Pct'] / 100.0)
    df['S1_Jet_Vol_Mt'] = df['S1_Total_Fuel_Mt'] * (1 - df['S1_SAF_Share_Pct'] / 100.0)
    
    # B. The Feedstock Wall Logic (HEFA Limit vs. Expensive PtL)
    # If Demand < Cap, price is HEFA. If Demand > Cap, excess is PtL.
    
    # Identify how much is cheap HEFA vs expensive PtL
    df['S1_Vol_HEFA_Mt'] = np.minimum(df['S1_SAF_Vol_Mt'], df['HEFA_EU_Supply_Cap_Mt'])
    df['S1_Vol_PtL_Mt'] = np.maximum(0, df['S1_SAF_Vol_Mt'] - df['HEFA_EU_Supply_Cap_Mt'])
    
    # Calculate Blended SAF Cost
    df['S1_SAF_Cost_Bn'] = (
        (df['S1_Vol_HEFA_Mt'] * df['Price_HEFA_USD']) + 
        (df['S1_Vol_PtL_Mt'] * df['Price_PtL_USD'])
    ) / 1000
    
    # Calculate Jet A-1 Cost
    df['S1_Jet_Cost_Bn'] = (df['S1_Jet_Vol_Mt'] * df['Price_JetA1_USD']) / 1000
    
    # C. Carbon Cost (S1 Emissions are lower, but price is same)
    df['S1_Carbon_Cost_Bn'] = (df['S1_CO2_Emissions_Mt'] * df['ETS_Paying_Ratio'] * df['Carbon_Price_USD']) / 1000
    
    # D. Hadi's Logistics Penalty (Only applies to S1, not S2)
    # Cost = SAF Volume * $150
    df['S1_Logistics_Penalty_Bn'] = (df['S1_SAF_Vol_Mt'] * df['Logistics_Penalty_USD_per_Tonne']) / 1000
    
    # E. Total S1 Cost
    df['S1_Total_Cost_Bn'] = (
        df['S1_Jet_Cost_Bn'] + 
        df['S1_SAF_Cost_Bn'] + 
        df['S1_Carbon_Cost_Bn'] + 
        df['S1_Logistics_Penalty_Bn']
    )
    
    # --- 6. METRICS FOR SLIDES ---
    # Calculate the "Green Premium" (Extra cost of S1 vs S0)
    df['Green_Premium_Bn'] = df['S1_Total_Cost_Bn'] - df['S0_Total_Cost_Bn']
    
    # Check if/when the "Wall" is hit
    df['Wall_Hit'] = df['S1_SAF_Vol_Mt'] > df['HEFA_EU_Supply_Cap_Mt']
    
    # --- 7. EXPORT ---
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    # --- 8. CONSOLE REPORT ---
    print("\n✅ Economic Calculation Complete!")
    print(f"   Output saved to: {output_path}")
    print("-" * 50)
    print("Summary Stats (Cumulative 2026-2050):")
    print(f"💰 Scenario 0 Total Cost:   ${df['S0_Total_Cost_Bn'].sum():.2f} Billion")
    print(f"💰 Scenario 1 Total Cost:   ${df['S1_Total_Cost_Bn'].sum():.2f} Billion")
    print(f"🛑 Logistics Penalty Paid:  ${df['S1_Logistics_Penalty_Bn'].sum():.2f} Billion")
    print(f"🧱 Feedstock Wall Hit in:    {df.loc[df['Wall_Hit'], 'Year'].min() if df['Wall_Hit'].any() else 'Never'}")
    print("-" * 50)

if __name__ == "__main__":
    calculate_economics()

