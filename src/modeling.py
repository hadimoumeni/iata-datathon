"""
Core modeling functions for the IEU Sustainability Datathon.

This module contains the logic for:
1. Forecasting air traffic and fuel demand.
2. Calculating the core required metrics for different scenarios.
3. Calculating the economic "differentiator" metrics for strategic analysis.
"""

import pandas as pd
from typing import Dict

# ==============================================================================
# --- 1. KEY ASSUMPTIONS & CONSTANTS ---
# Centralizing assumptions here makes the model transparent and easy to adjust.
# Sources for these values should be documented in the final report.
# ==============================================================================

# Emission Factors (tonnes of CO2 per tonne of fuel)
JET_A1_EMISSION_FACTOR = 3.16
# Represents a lifecycle emissions reduction of 80% compared to conventional fuel.
SAF_LIFECYCLE_EMISSION_FACTOR = 3.16 * (1 - 0.80)

# Efficiency Improvement Assumptions (Annual Reduction)
AIRCRAFT_TECH_EFFICIENCY_GAIN = 0.015  # 1.5% annual improvement from new aircraft
OPERATIONAL_EFFICIENCY_GAIN = 0.07     # 7% total potential gain from SESAR by 2040

# Economic Assumptions
# NOTE: These are simplified. A more advanced model could use dynamic price forecasts.
JET_A1_PRICE_PER_TONNE = 1000  # Example: €1000 / tonne
SAF_PRICE_PREMIUM = 2.5        # SAF is 2.5x the price of conventional jet fuel
SAF_PRICE_PER_TONNE = JET_A1_PRICE_PER_TONNE * SAF_PRICE_PREMIUM

# EU ETS Carbon Price Forecast (€ per tonne of CO2)
# Simplified linear forecast from ~€80 in 2025 to ~€150 in 2050
CARBON_PRICE_FORECAST = {year: 80 + 2.8 * (year - 2025) for year in range(2025, 2051)}

# Scenario Mandates
S1_MANDATES = {
    2025: 0.02, 2030: 0.06, 2035: 0.20, 2040: 0.34, 2045: 0.42, 2050: 0.70
}
# A low, hypothetical voluntary adoption rate for the "Market-Driven" scenario
S0_VOLUNTARY_ADOPTION = 0.01


# ==============================================================================
# --- 2. CORE MODELING FUNCTIONS ---
# ==============================================================================

def calculate_fuel_demand(
    base_demand_2025: float,
    annual_growth_rate: float,
    apply_operational_gains: bool = False
) -> pd.DataFrame:
    """
    Calculates the total fuel demand from 2025 to 2050.

    Args:
        base_demand_2025 (float): The total fuel demand in the base year (2025) in Mt.
        annual_growth_rate (float): The projected annual growth rate for air traffic.
        apply_operational_gains (bool): If True, applies additional efficiency gains
                                        from operational improvements (e.g., SESAR).

    Returns:
        pd.DataFrame: A DataFrame with columns 'Year' and 'Total_Fuel_Demand_Mt'.
    """
    years = range(2025, 2051)
    df = pd.DataFrame({'Year': years})
    df.set_index('Year', inplace=True)

    # 1. Calculate raw demand based on traffic growth
    df['Raw_Demand_Mt'] = [base_demand_2025 * ((1 + annual_growth_rate) ** i) for i in range(len(years))]

    # 2. Apply annual efficiency gains from aircraft technology
    df['Tech_Efficiency_Factor'] = [(1 - AIRCRAFT_TECH_EFFICIENCY_GAIN) ** i for i in range(len(years))]
    df['Demand_After_Tech_Gains_Mt'] = df['Raw_Demand_Mt'] * df['Tech_Efficiency_Factor']

    # 3. (Optional) Apply operational efficiency gains for advanced scenarios
    if apply_operational_gains:
        # Simplified linear ramp-up of operational gains to the max potential by 2040
        op_gains = [min(OPERATIONAL_EFFICIENCY_GAIN, (OPERATIONAL_EFFICIENCY_GAIN / 15) * (year - 2025)) for year in years]
        df['Operational_Efficiency_Factor'] = 1 - pd.Series(op_gains, index=years)
        df['Total_Fuel_Demand_Mt'] = df['Demand_After_Tech_Gains_Mt'] * df['Operational_Efficiency_Factor']
    else:
        df['Total_Fuel_Demand_Mt'] = df['Demand_After_Tech_Gains_Mt']

    return df[['Total_Fuel_Demand_Mt']]


def run_scenario_analysis(
    fuel_demand_df: pd.DataFrame,
    scenario_name: str
) -> pd.DataFrame:
    """
    Runs a full scenario analysis, calculating all core and economic metrics.

    Args:
        fuel_demand_df (pd.DataFrame): DataFrame from calculate_fuel_demand.
        scenario_name (str): The name of the scenario ('S0', 'S1', or 'S2').

    Returns:
        pd.DataFrame: A comprehensive DataFrame with all calculated metrics for the scenario.
    """
    results = fuel_demand_df.copy()

    # --- Determine SAF Blending Share based on scenario ---
    if scenario_name == 'S0':
        results['SAF_Blending_Share_%'] = S0_VOLUNTARY_ADOPTION
    elif scenario_name in ['S1', 'S2']:
        # Interpolate mandates for years between the specified points
        mandate_series = pd.Series(S1_MANDATES)
        mandate_series = mandate_series.reindex(range(2025, 2051)).interpolate()
        results['SAF_Blending_Share_%'] = mandate_series
    else:
        raise ValueError("Scenario name must be 'S0', 'S1', or 'S2'.")

    # --- Calculate Core Required Metrics ---
    results['SAF_Volume_Mt'] = results['Total_Fuel_Demand_Mt'] * results['SAF_Blending_Share_%']
    results['Jet_Fuel_Volume_Mt'] = results['Total_Fuel_Demand_Mt'] - results['SAF_Volume_Mt']

    results['CO2_Emissions_Generated_Mt'] = (results['Jet_Fuel_Volume_Mt'] * JET_A1_EMISSION_FACTOR) + \
                                          (results['SAF_Volume_Mt'] * SAF_LIFECYCLE_EMISSION_FACTOR)

    co2_if_no_saf = results['Total_Fuel_Demand_Mt'] * JET_A1_EMISSION_FACTOR
    results['CO2_Emissions_Avoided_Mt'] = co2_if_no_saf - results['CO2_Emissions_Generated_Mt']
    
    # Ensure no negative avoidance due to rounding
    results['CO2_Emissions_Avoided_Mt'] = results['CO2_Emissions_Avoided_Mt'].clip(lower=0)

    # --- Calculate "Winning" Differentiator Metrics ---
    results['Carbon_Price_EUR_per_Ton'] = results.index.map(CARBON_PRICE_FORECAST)

    results['Total_Fuel_Cost_EUR_Bn'] = ((results['Jet_Fuel_Volume_Mt'] * JET_A1_PRICE_PER_TONNE) + \
                                       (results['SAF_Volume_Mt'] * SAF_PRICE_PER_TONNE)) / 1e9

    results['Carbon_Cost_EUR_Bn'] = (results['CO2_Emissions_Generated_Mt'] * results['Carbon_Price_EUR_per_Ton']) / 1e9

    results['Total_Cost_of_Compliance_EUR_Bn'] = results['Total_Fuel_Cost_EUR_Bn'] + results['Carbon_Cost_EUR_Bn']
    
    # --- Final Formatting ---
    # Convert share to percentage for clarity in outputs
    results['SAF_Blending_Share_%'] *= 100

    return results


# ==============================================================================
# --- 3. EXAMPLE USAGE BLOCK ---
# This allows the script to be run directly to test the functions.
# ==============================================================================
if __name__ == '__main__':
    # --- Example Parameters ---
    BASE_DEMAND = 80.0  # Example: 80 Mt of fuel in 2025
    TRAFFIC_GROWTH = 0.025 # Example: 2.5% annual growth in traffic

    print("--- Running Model Test ---")
    print(f"Base Assumptions:\n- Base Demand (2025): {BASE_DEMAND} Mt\n- Traffic Growth: {TRAFFIC_GROWTH*100}%\n")

    # --- Calculate Fuel Demand for different scenarios ---
    # S0 and S1 use the standard demand forecast
    base_fuel_demand = calculate_fuel_demand(BASE_DEMAND, TRAFFIC_GROWTH, apply_operational_gains=False)
    # S2 includes the operational efficiency gains
    ops_efficient_fuel_demand = calculate_fuel_demand(BASE_DEMAND, TRAFFIC_GROWTH, apply_operational_gains=True)

    # --- Run each scenario ---
    s0_results = run_scenario_analysis(base_fuel_demand, 'S0')
    s1_results = run_scenario_analysis(base_fuel_demand, 'S1')
    s2_results = run_scenario_analysis(ops_efficient_fuel_demand, 'S2') # Note: uses the efficient demand

    print("\n--- S1 Scenario Results (Sample) ---")
    print(s1_results.loc[[2025, 2030, 2035, 2050]].round(2))
    
    print("\n--- S2 Scenario Results (Sample) ---")
    print(s2_results.loc[[2025, 2030, 2035, 2050]].round(2))

    print("\n--- Model Test Complete ---")
