import pandas as pd
import numpy as np
import os

# --- Global modelling assumptions for Objective 2 (S1+S2 economics) ---
# These are central values; ranges and sources are documented in economic_sources.yaml
# and in the project report / notebook.

# 1. Logistics distance assumption for moving SAF to EU hubs
#    (tonne-kilometres of logistics per tonne of SAF delivered)
LOGISTICS_TKM_PER_TONNE = 1000.0  # t-km / t SAF

# 2. Global HEFA supply cap (for narrative only – EU cap is in the CSV)
HEFA_GLOBAL_SUPPLY_CAP_MT = 30.0  # Mt / year (illustrative central value)

# 3. Smart Levy (S2) parameters
#    - PASSENGERS_EU27_2023_M: EU27 passengers carried by air in 2023 (~973m, Eurostat)
#    - LEVY_EUR_PER_PAX: central Smart Levy level per passenger
#    - LEVY_TO_SAF_SHARE: share of levy revenue earmarked for buying down SAF prices
PASSENGERS_EU27_2023_M = 973.0   # million passengers / year
LEVY_EUR_PER_PAX = 15.0          # €/pax (central value, within 7.40–40 range)
LEVY_TO_SAF_SHARE = 0.8          # 80% of levy revenue used for SAF subsidies


def calculate_economics():
    """Builds Objective 2 economic metrics for:
       - S0: BAU
       - S1: Policy-mandated SAF
       - S2: Smart-Levy scenario (levy-funded SAF subsidies on top of S1 volumes)
    """
    # --- 1. SETUP PATHS ---
    obj1_path = 'data/metrics/obj1_official_output__eu27__annual__2026-2050.csv'
    economics_path = 'data/clean/layer3_economic_assumptions.csv'
    output_path = 'data/metrics/obj2_economic_results.csv'

    # Check existence
    if not os.path.exists(obj1_path):
        print(f"❌ Error: Could not find Objective 1 data at {obj1_path}")
        print("   Please ensure your 'Total_Fuel' and 'SAF_Share' data is ready.")
        return

    if not os.path.exists(economics_path):
        print(f"❌ Error: Could not find Economic data at {economics_path}")
        return

    # --- 2. LOAD DATA ---
    print("🔄 Loading datasets...")
    df_vol = pd.read_csv(obj1_path)           # Obj1 volumes (fuel, emissions)
    df_price = pd.read_csv(economics_path)    # Layer-3 economic assumptions

    # Obj1 has: Year, Scenario (0/1), Total_Fuel, SAF_Share, CO2_Emissions, Avoided_CO2
    df_s0 = df_vol[df_vol["Scenario"] == 0].copy()
    df_s1 = df_vol[df_vol["Scenario"] == 1].copy()

    # Rename S0 columns
    df_s0 = df_s0.rename(
        columns={
            "Total_Fuel": "S0_Total_Fuel_Mt",
            "SAF_Share": "S0_SAF_Share_Pct",
            "CO2_Emissions": "S0_CO2_Emissions_Mt",
            "Avoided_CO2": "S0_Avoided_CO2_Mt",
        }
    )

    # Rename S1 columns
    df_s1 = df_s1.rename(
        columns={
            "Total_Fuel": "S1_Total_Fuel_Mt",
            "SAF_Share": "S1_SAF_Share_Pct",
            "CO2_Emissions": "S1_CO2_Emissions_Mt",
            "Avoided_CO2": "S1_Avoided_CO2_Mt",
        }
    )

    # Merge S0 & S1 on Year
    df_scenarios = pd.merge(
        df_s0[["Year", "S0_Total_Fuel_Mt", "S0_SAF_Share_Pct", "S0_CO2_Emissions_Mt"]],
        df_s1[["Year", "S1_Total_Fuel_Mt", "S1_SAF_Share_Pct", "S1_CO2_Emissions_Mt"]],
        on="Year",
        how="inner",
    )

    # Merge with price / economic assumptions
    df = pd.merge(df_scenarios, df_price, on="Year", how="inner")

    # --- 3. ETS PAYING RATIO (phase-out of free allowances) ---
    # 50% free in 2025, 0% free from 2026 onward → Paying_Ratio 0.5 → 1.0.
    df["ETS_Paying_Ratio"] = np.where(df["Year"] == 2025, 0.5, 1.0)

    # --- 4. S0 (BAU) COSTS ---
    # Fuel cost: assume effectively all Jet A-1 for S0
    df["S0_Fuel_Cost_Bn"] = (df["S0_Total_Fuel_Mt"] * df["Price_JetA1_USD"]) / 1000.0

    # Carbon cost
    df["S0_Carbon_Cost_Bn"] = (
        df["S0_CO2_Emissions_Mt"] * df["ETS_Paying_Ratio"] * df["Carbon_Price_USD"]
    ) / 1000.0

    df["S0_Total_Cost_Bn"] = df["S0_Fuel_Cost_Bn"] + df["S0_Carbon_Cost_Bn"]

    # --- 5. S1 (POLICY MANDATE) COSTS & LAYER 3 INPUTS ---

    # Volumes
    df["S1_SAF_Vol_Mt"] = df["S1_Total_Fuel_Mt"] * (df["S1_SAF_Share_Pct"] / 100.0)
    df["S1_Jet_Vol_Mt"] = df["S1_Total_Fuel_Mt"] - df["S1_SAF_Vol_Mt"]

    # Feedstock wall: HEFA vs PtL volumes
    df["S1_Vol_HEFA_Mt"] = np.minimum(df["S1_SAF_Vol_Mt"], df["HEFA_EU_Supply_Cap_Mt"])
    df["S1_Vol_PtL_Mt"] = np.maximum(
        0.0, df["S1_SAF_Vol_Mt"] - df["HEFA_EU_Supply_Cap_Mt"]
    )

    # SAF cost split
    df["S1_SAF_Cost_Bn"] = (
        df["S1_Vol_HEFA_Mt"] * df["Price_HEFA_USD"]
        + df["S1_Vol_PtL_Mt"] * df["Price_PtL_USD"]
    ) / 1000.0

    # Jet A-1 cost in S1
    df["S1_Jet_Cost_Bn"] = (df["S1_Jet_Vol_Mt"] * df["Price_JetA1_USD"]) / 1000.0

    # Carbon cost in S1
    df["S1_Carbon_Cost_Bn"] = (
        df["S1_CO2_Emissions_Mt"] * df["ETS_Paying_Ratio"] * df["Carbon_Price_USD"]
    ) / 1000.0

    # Logistics cost penalty (input is $/t SAF)
    df["S1_Logistics_Penalty_Bn"] = (
        df["S1_SAF_Vol_Mt"] * df["Logistics_Penalty_USD_per_Tonne"]
    ) / 1000.0

    # Logistics *emissions* (t-km × gCO2/t-km → Mt CO2)
    df["S1_Logistics_Emissions_Mt"] = (
        df["S1_SAF_Vol_Mt"]
        * LOGISTICS_TKM_PER_TONNE
        * df["Logistics_Emissions_gCO2_per_tkm"]
    ) / 1_000_000.0

    # Monetised carbon cost of logistics emissions
    df["S1_Logistics_Carbon_Cost_Bn"] = (
        df["S1_Logistics_Emissions_Mt"]
        * df["ETS_Paying_Ratio"]
        * df["Carbon_Price_USD"]
    ) / 1000.0

    # Total S1 cost from airline/system perspective (fuel + carbon + logistics *cost*)
    df["S1_Total_Fuel_Cost_Bn"] = df["S1_Jet_Cost_Bn"] + df["S1_SAF_Cost_Bn"]
    df["S1_Total_Cost_Bn"] = (
        df["S1_Total_Fuel_Cost_Bn"]
        + df["S1_Carbon_Cost_Bn"]
        + df["S1_Logistics_Penalty_Bn"]
    )

    # Feedstock wall indicator
    df["Wall_Hit"] = df["S1_SAF_Vol_Mt"] > df["HEFA_EU_Supply_Cap_Mt"]

    # --- 6. LAYER-3 METRICS FOR S0/S1 ---

    # Green premium of S1 vs S0
    df["Green_Premium_Bn"] = df["S1_Total_Cost_Bn"] - df["S0_Total_Cost_Bn"]

    # CO2 avoided vs BAU (physical emissions)
    df["CO2_Avoided_Mt"] = df["S0_CO2_Emissions_Mt"] - df["S1_CO2_Emissions_Mt"]

    # Cost per ton of CO2 abated for S1
    df["Cost_per_tCO2_Abated_USD"] = np.where(
        df["CO2_Avoided_Mt"] > 0,
        (df["Green_Premium_Bn"] * 1000.0) / df["CO2_Avoided_Mt"],
        np.nan,
    )

    # Narrative-only global HEFA cap (same value for all rows)
    df["HEFA_Global_Supply_Cap_Mt"] = HEFA_GLOBAL_SUPPLY_CAP_MT

    # --- 7. S2 (SMART LEVY) CALCULATIONS ---

    # We keep the S1 physical volumes/emissions, but introduce a passenger levy
    # that generates revenue and is partly used to subsidise SAF prices.

    # A. Levy and passenger assumptions
    df["S2_Passengers_M"] = PASSENGERS_EU27_2023_M
    df["S2_Levy_EUR_per_pax"] = LEVY_EUR_PER_PAX
    df["S2_Levy_USD_per_pax"] = df["S2_Levy_EUR_per_pax"] * df["Exchange_Rate_USD_EUR"]

    # Levy revenue in billions of USD (passengers are in millions)
    df["S2_Levy_Annual_Revenue_Bn"] = (
        df["S2_Passengers_M"] * df["S2_Levy_USD_per_pax"]
    ) / 1000.0

    # Fraction of levy revenue allocated to SAF subsidies
    df["S2_SAF_Subsidy_Pool_Bn"] = df["S2_Levy_Annual_Revenue_Bn"] * LEVY_TO_SAF_SHARE

    # B. Unsubsidised realised SAF price in S1 (blended HEFA+PtL)
    df["S1_Realised_SAF_Price_USD_per_t"] = np.where(
        df["S1_SAF_Vol_Mt"] > 0,
        (df["S1_SAF_Cost_Bn"] * 1000.0) / df["S1_SAF_Vol_Mt"],
        np.nan,
    )

    # C. Subsidy per tonne of SAF under S2
    df["S2_SAF_Subsidy_USD_per_t"] = np.where(
        df["S1_SAF_Vol_Mt"] > 0,
        (df["S2_SAF_Subsidy_Pool_Bn"] * 1000.0) / df["S1_SAF_Vol_Mt"],
        0.0,
    )

    # Cap subsidy so effective price cannot go negative
    df["S2_SAF_Subsidy_USD_per_t"] = np.minimum(
        df["S2_SAF_Subsidy_USD_per_t"], df["S1_Realised_SAF_Price_USD_per_t"]
    )

    # D. Effective SAF price & fuel bill under S2 (airline perspective)
    df["S2_Effective_SAF_Price_USD_per_t"] = (
        df["S1_Realised_SAF_Price_USD_per_t"] - df["S2_SAF_Subsidy_USD_per_t"]
    )

    df["S2_SAF_Cost_Bn"] = (
        df["S2_Effective_SAF_Price_USD_per_t"] * df["S1_SAF_Vol_Mt"]
    ) / 1000.0

    df["S2_Jet_Cost_Bn"] = df["S1_Jet_Cost_Bn"]
    df["S2_Total_Fuel_Cost_Bn"] = df["S2_Jet_Cost_Bn"] + df["S2_SAF_Cost_Bn"]

    # Carbon & logistics penalties are unchanged in S2 (same physical emissions & SAF tonnage)
    df["S2_Carbon_Cost_Bn"] = df["S1_Carbon_Cost_Bn"]
    df["S2_Logistics_Penalty_Bn"] = df["S1_Logistics_Penalty_Bn"]
    df["S2_Logistics_Emissions_Mt"] = df["S1_Logistics_Emissions_Mt"]
    df["S2_Logistics_Carbon_Cost_Bn"] = df["S1_Logistics_Carbon_Cost_Bn"]

    # Total cost for airlines in S2 (excluding levy paid by passengers)
    df["S2_Total_Cost_Bn"] = (
        df["S2_Total_Fuel_Cost_Bn"]
        + df["S2_Carbon_Cost_Bn"]
        + df["S2_Logistics_Penalty_Bn"]
    )

    # Optional system-wide total including levy burden on passengers
    df["S2_Total_Cost_Incl_Levy_Bn"] = df["S2_Total_Cost_Bn"] + df["S2_Levy_Annual_Revenue_Bn"]

    # Layer-3 KPIs for S2
    df["S2_Green_Premium_Bn"] = df["S2_Total_Cost_Bn"] - df["S0_Total_Cost_Bn"]
    df["S2_Cost_per_tCO2_Abated_USD"] = np.where(
        df["CO2_Avoided_Mt"] > 0,
        (df["S2_Green_Premium_Bn"] * 1000.0) / df["CO2_Avoided_Mt"],
        np.nan,
    )

    # --- 8. EXPORT ---
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    # --- 9. CONSOLE REPORT ---
    print("\n✅ Economic Calculation Complete!")
    print(f"   Output saved to: {output_path}")
    print("-" * 50)
    print("Summary Stats (Cumulative 2026-2050):")
    print(f"💰 S0 Total Cost:             ${df['S0_Total_Cost_Bn'].sum():.2f} Billion")
    print(f"💰 S1 Total Cost:             ${df['S1_Total_Cost_Bn'].sum():.2f} Billion")
    print(f"💰 S2 Total Cost (airlines):  ${df['S2_Total_Cost_Bn'].sum():.2f} Billion")
    print(f"💰 S2 Levy Revenue:           ${df['S2_Levy_Annual_Revenue_Bn'].sum():.2f} Billion")
    print(f"🛑 Logistics Penalty (S1/S2): ${df['S1_Logistics_Penalty_Bn'].sum():.2f} Billion")
    print(
        "🧱 Feedstock Wall Hit in:     "
        + f"{df.loc[df['Wall_Hit'], 'Year'].min() if df['Wall_Hit'].any() else 'Never'}"
    )
    print("-" * 50)


if __name__ == "__main__":
    calculate_economics()
