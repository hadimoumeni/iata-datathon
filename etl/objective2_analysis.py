"""
Objective 2 – Scenario comparison & visualization

This script:

- Loads data/metrics/obj2_economic_results.csv (output of objective2_calc.py)

- Builds summary tables for S0, S1, S2 (cumulative + key year)

- Creates a set of plots to visually compare scenarios:

    * Total cost over time

    * Cost components for a key year

    * Cost per tCO2 abated (S1 vs S2)

    * SAF vs Jet A-1 prices (S0/S1/S2 economics)

    * HEFA feedstock wall (HEFA vs PtL volumes)

- Prints summary tables to the console (Markdown if possible)

- Saves figures into ./figures/

The goal is to provide all evidence needed that S2 (Smart Levy) is

economically preferable to pure S1, while delivering the same CO2 reductions.

"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

DATA_PATH = Path("data/metrics/obj2_economic_results.csv")
FIG_DIR = Path("figures")
KEY_YEAR = 2030  # key "story year" for bar charts / tables

# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load Objective 2 results CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Could not find Objective 2 results at: {path}")
    df = pd.read_csv(path)
    return df

def print_markdown_table(df: pd.DataFrame, title: str | None = None):
    """Print a DataFrame as a Markdown table if possible, otherwise as plain text."""
    if title:
        print("\n" + "=" * len(title))
        print(title)
        print("=" * len(title))
    try:
        # Requires optional dependency 'tabulate'
        print(df.to_markdown(index=True))
    except Exception:
        print(df.to_string(index=True))

# ---------------------------------------------------------------------
# Summary tables
# ---------------------------------------------------------------------

def build_cumulative_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build cumulative (2026-2050) scenario comparison table.

    Outputs a DataFrame with rows: S0, S1, S2
    and columns:

        - Total_Cost_Bn
        - Total_Cost_Incl_Levy_Bn (only for S2, others = Total_Cost_Bn)
        - Green_Premium_vs_S0_Bn
        - Total_Emissions_Mt
        - Total_CO2_Avoided_vs_S0_Mt
        - Cost_per_tCO2_Abated_USD
        - Total_Levy_Revenue_Bn
        - Avg_SAF_Price_USD_per_t (S1) / Avg_Effective_SAF_Price_USD_per_t (S2)
    """
    # Cumulative costs
    s0_total_cost = df["S0_Total_Cost_Bn"].sum()
    s1_total_cost = df["S1_Total_Cost_Bn"].sum()
    s2_total_cost = df["S2_Total_Cost_Bn"].sum()
    s2_total_cost_incl_levy = df["S2_Total_Cost_Incl_Levy_Bn"].sum()

    # Cumulative emissions
    s0_total_emissions = df["S0_CO2_Emissions_Mt"].sum()
    s1_total_emissions = df["S1_CO2_Emissions_Mt"].sum()
    s2_total_emissions = s1_total_emissions  # S2 has same physical emissions as S1

    total_co2_avoided = s0_total_emissions - s1_total_emissions  # same for S1 & S2

    # Green premiums
    s1_green_premium = s1_total_cost - s0_total_cost
    s2_green_premium = s2_total_cost - s0_total_cost

    # Cost per tCO2 abated (cumulative)
    if total_co2_avoided > 0:
        s1_cost_per_t = (s1_green_premium * 1000.0) / total_co2_avoided
        s2_cost_per_t = (s2_green_premium * 1000.0) / total_co2_avoided
    else:
        s1_cost_per_t = np.nan
        s2_cost_per_t = np.nan

    # Cumulative levy revenue (S2 only)
    total_levy_revenue = df["S2_Levy_Annual_Revenue_Bn"].sum()

    # Average prices (simple average over years)
    avg_s1_saf_price = df["S1_Realised_SAF_Price_USD_per_t"].mean()
    avg_s2_saf_price = df["S2_Effective_SAF_Price_USD_per_t"].mean()

    summary = pd.DataFrame(
        {
            "Total_Cost_Bn": [
                s0_total_cost,
                s1_total_cost,
                s2_total_cost,
            ],
            "Total_Cost_Incl_Levy_Bn": [
                s0_total_cost,
                s1_total_cost,
                s2_total_cost_incl_levy,
            ],
            "Green_Premium_vs_S0_Bn": [
                0.0,
                s1_green_premium,
                s2_green_premium,
            ],
            "Total_Emissions_Mt": [
                s0_total_emissions,
                s1_total_emissions,
                s2_total_emissions,
            ],
            "Total_CO2_Avoided_vs_S0_Mt": [
                0.0,
                total_co2_avoided,
                total_co2_avoided,
            ],
            "Cost_per_tCO2_Abated_USD": [
                np.nan,
                s1_cost_per_t,
                s2_cost_per_t,
            ],
            "Total_Levy_Revenue_Bn": [
                0.0,
                0.0,
                total_levy_revenue,
            ],
            "Avg_SAF_Price_USD_per_t": [
                np.nan,
                avg_s1_saf_price,
                avg_s2_saf_price,
            ],
        },
        index=["S0_BAU", "S1_Mandate", "S2_SmartLevy"],
    )

    return summary

def build_year_summary(df: pd.DataFrame, year: int = KEY_YEAR) -> pd.DataFrame:
    """
    Build per-scenario summary for a single year (e.g. 2030).

    Outputs a DataFrame with:

        - Total_Cost_Bn
        - Fuel_Cost_Bn
        - Carbon_Cost_Bn
        - Logistics_Cost_Bn
        - Levy_Revenue_Bn (system view)
        - CO2_Emissions_Mt
        - CO2_Avoided_vs_S0_Mt
        - Cost_per_tCO2_Abated_USD
        - SAF_Price_USD_per_t (S1/S2)
    """
    row = df.loc[df["Year"] == year].copy()
    if row.empty:
        raise ValueError(f"No data for Year={year} in Objective 2 results.")
    row = row.iloc[0]

    s0_cost = row["S0_Total_Cost_Bn"]
    s1_cost = row["S1_Total_Cost_Bn"]
    s2_cost = row["S2_Total_Cost_Bn"]

    # Breakdowns
    s0_fuel = row["S0_Fuel_Cost_Bn"]
    s0_carbon = row["S0_Carbon_Cost_Bn"]
    s0_logistics = 0.0

    s1_fuel = row["S1_Total_Fuel_Cost_Bn"]
    s1_carbon = row["S1_Carbon_Cost_Bn"]
    s1_logistics = row["S1_Logistics_Penalty_Bn"]

    s2_fuel = row["S2_Total_Fuel_Cost_Bn"]
    s2_carbon = row["S2_Carbon_Cost_Bn"]
    s2_logistics = row["S2_Logistics_Penalty_Bn"]

    # Emissions
    s0_emissions = row["S0_CO2_Emissions_Mt"]
    s1_emissions = row["S1_CO2_Emissions_Mt"]
    s2_emissions = s1_emissions

    co2_avoided = s0_emissions - s1_emissions

    # Cost per tCO2
    s1_cost_per_t = (
        (s1_cost - s0_cost) * 1000.0 / co2_avoided if co2_avoided > 0 else np.nan
    )
    s2_cost_per_t = (
        (s2_cost - s0_cost) * 1000.0 / co2_avoided if co2_avoided > 0 else np.nan
    )

    # Levy
    s2_levy = row["S2_Levy_Annual_Revenue_Bn"]

    summary = pd.DataFrame(
        {
            "Total_Cost_Bn": [s0_cost, s1_cost, s2_cost],
            "Fuel_Cost_Bn": [s0_fuel, s1_fuel, s2_fuel],
            "Carbon_Cost_Bn": [s0_carbon, s1_carbon, s2_carbon],
            "Logistics_Cost_Bn": [s0_logistics, s1_logistics, s2_logistics],
            "Levy_Revenue_Bn": [0.0, 0.0, s2_levy],
            "CO2_Emissions_Mt": [s0_emissions, s1_emissions, s2_emissions],
            "CO2_Avoided_vs_S0_Mt": [0.0, co2_avoided, co2_avoided],
            "Cost_per_tCO2_Abated_USD": [np.nan, s1_cost_per_t, s2_cost_per_t],
            "SAF_Price_USD_per_t": [
                np.nan,
                row["S1_Realised_SAF_Price_USD_per_t"],
                row["S2_Effective_SAF_Price_USD_per_t"],
            ],
        },
        index=["S0_BAU", "S1_Mandate", "S2_SmartLevy"],
    )

    return summary

# ---------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------

def plot_total_costs(df: pd.DataFrame, out_dir: Path = FIG_DIR):
    """Line plot of total cost by scenario over time."""
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.plot(df["Year"], df["S0_Total_Cost_Bn"], label="S0 – BAU")
    plt.plot(df["Year"], df["S1_Total_Cost_Bn"], label="S1 – Mandate")
    plt.plot(df["Year"], df["S2_Total_Cost_Bn"], label="S2 – Smart Levy (airlines)")
    plt.xlabel("Year")
    plt.ylabel("Total cost (Bn USD)")
    plt.title("Total System Cost by Scenario (Airline Perspective)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir / "total_costs_scenario_comparison.png", dpi=300)
    plt.close()

def plot_cost_components_year(df: pd.DataFrame, year: int = KEY_YEAR, out_dir: Path = FIG_DIR):
    """Stacked bar chart of cost components for S0, S1, S2 in a given year."""
    out_dir.mkdir(parents=True, exist_ok=True)

    row = df.loc[df["Year"] == year].copy()
    if row.empty:
        raise ValueError(f"No data for Year={year}")

    row = row.iloc[0]

    scenarios = ["S0 – BAU", "S1 – Mandate", "S2 – Smart Levy"]
    x = np.arange(len(scenarios))

    fuel = np.array([
        row["S0_Fuel_Cost_Bn"],
        row["S1_Total_Fuel_Cost_Bn"],
        row["S2_Total_Fuel_Cost_Bn"],
    ])

    carbon = np.array([
        row["S0_Carbon_Cost_Bn"],
        row["S1_Carbon_Cost_Bn"],
        row["S2_Carbon_Cost_Bn"],
    ])

    logistics = np.array([
        0.0,
        row["S1_Logistics_Penalty_Bn"],
        row["S2_Logistics_Penalty_Bn"],
    ])

    # Levy is not a cost to airlines but a burden on passengers (system view)
    levy = np.array([
        0.0,
        0.0,
        row["S2_Levy_Annual_Revenue_Bn"],
    ])

    width = 0.6

    plt.figure(figsize=(8, 5))
    plt.bar(x, fuel, width, label="Fuel cost")
    plt.bar(x, carbon, width, bottom=fuel, label="Carbon cost")
    plt.bar(x, logistics, width, bottom=fuel + carbon, label="Logistics cost")
    plt.bar(
        x,
        levy,
        width,
        bottom=fuel + carbon + logistics,
        label="Levy (passenger burden)",
        alpha=0.4,
        edgecolor="black",
        linestyle="--",
    )

    plt.xticks(x, scenarios, rotation=10)
    plt.ylabel("Cost (Bn USD)")
    plt.title(f"Cost Breakdown by Scenario in {year}")
    plt.legend()
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir / f"cost_breakdown_{year}.png", dpi=300)
    plt.close()

def plot_cost_per_tco2(df: pd.DataFrame, out_dir: Path = FIG_DIR):
    """Line plot of cost per tCO2 abated for S1 vs S2 over time."""
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.plot(df["Year"], df["Cost_per_tCO2_Abated_USD"], label="S1 – Mandate")
    plt.plot(df["Year"], df["S2_Cost_per_tCO2_Abated_USD"], label="S2 – Smart Levy")
    plt.xlabel("Year")
    plt.ylabel("Cost per tCO₂ abated (USD/tCO₂)")
    plt.title("Cost Efficiency of Emissions Reductions (S1 vs S2)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir / "cost_per_tco2_s1_vs_s2.png", dpi=300)
    plt.close()

def plot_saf_prices(df: pd.DataFrame, out_dir: Path = FIG_DIR):
    """Line plot of Jet A-1 price, S1 realised SAF price, and S2 effective SAF price."""
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.plot(df["Year"], df["Price_JetA1_USD"], label="Jet A-1 list price")
    plt.plot(df["Year"], df["S1_Realised_SAF_Price_USD_per_t"], label="S1 SAF blended price")
    plt.plot(df["Year"], df["S2_Effective_SAF_Price_USD_per_t"], label="S2 SAF effective price")
    plt.xlabel("Year")
    plt.ylabel("Price (USD per tonne)")
    plt.title("Jet A-1 vs SAF Prices (S1 vs S2)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir / "saf_vs_jet_prices.png", dpi=300)
    plt.close()

def plot_feedstock_wall(df: pd.DataFrame, out_dir: Path = FIG_DIR):
    """Visualize HEFA vs PtL volumes and the HEFA EU cap over time."""
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    years = df["Year"]

    # Stack HEFA and PtL SAF volumes
    hefa = df["S1_Vol_HEFA_Mt"]
    ptl = df["S1_Vol_PtL_Mt"]
    cap = df["HEFA_EU_Supply_Cap_Mt"]

    plt.fill_between(years, 0, hefa, alpha=0.5, label="HEFA SAF volume (S1)")
    plt.fill_between(years, hefa, hefa + ptl, alpha=0.5, label="PtL SAF volume (S1)")
    plt.plot(years, cap, linestyle="--", label="HEFA EU supply cap")

    plt.xlabel("Year")
    plt.ylabel("SAF volume (Mt)")
    plt.title("HEFA Feedstock Wall and PtL Ramp-up (Scenario 1)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir / "feedstock_wall_hefa_ptl.png", dpi=300)
    plt.close()

def plot_table_as_image(df: pd.DataFrame, title: str, out_path: Path, figsize=(14, 6)):
    """Create a PNG visualization of a DataFrame table."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis('tight')
    ax.axis('off')
    
    # Prepare data for display (round numbers, format)
    display_df = df.copy()
    for col in display_df.columns:
        if display_df[col].dtype in ['float64', 'float32']:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) and abs(x) < 1000 else f"{x:,.0f}" if pd.notna(x) else "—")
    
    # Create table
    table = ax.table(
        cellText=display_df.values,
        rowLabels=display_df.index,
        colLabels=display_df.columns,
        cellLoc='center',
        loc='center',
        bbox=[0, 0, 1, 1]
    )
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Color header row
    for i in range(len(display_df.columns)):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Color row labels
    for i in range(len(display_df.index)):
        table[(i+1, -1)].set_facecolor('#D9E1F2')
        table[(i+1, -1)].set_text_props(weight='bold')
    
    # Alternate row colors for readability
    for i in range(1, len(display_df) + 1):
        if i % 2 == 0:
            for j in range(len(display_df.columns)):
                table[(i, j)].set_facecolor('#F2F2F2')
    
    # Add title
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_cumulative_summary_table(cumulative_summary: pd.DataFrame, out_dir: Path = FIG_DIR):
    """Visualize cumulative summary table as PNG."""
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_table_as_image(
        cumulative_summary,
        "Cumulative Scenario Summary (2026–2050)",
        out_dir / "table_cumulative_summary.png",
        figsize=(16, 5)
    )

def plot_year_summary_table(year_summary: pd.DataFrame, year: int = KEY_YEAR, out_dir: Path = FIG_DIR):
    """Visualize year summary table as PNG."""
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_table_as_image(
        year_summary,
        f"Scenario Summary – Year {year}",
        out_dir / f"table_year_summary_{year}.png",
        figsize=(16, 5)
    )

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    df = load_data()

    # 1) Summary tables
    cumulative_summary = build_cumulative_summary(df)
    year_summary = build_year_summary(df, year=KEY_YEAR)

    print_markdown_table(cumulative_summary, title="Cumulative Scenario Summary (2026–2050)")
    print_markdown_table(year_summary, title=f"Scenario Summary – Year {KEY_YEAR}")

    # 2) Plots
    plot_total_costs(df, FIG_DIR)
    plot_cost_components_year(df, year=KEY_YEAR, out_dir=FIG_DIR)
    plot_cost_per_tco2(df, FIG_DIR)
    plot_saf_prices(df, FIG_DIR)
    plot_feedstock_wall(df, FIG_DIR)
    
    # 3) Table visualizations
    plot_cumulative_summary_table(cumulative_summary, FIG_DIR)
    plot_year_summary_table(year_summary, year=KEY_YEAR, out_dir=FIG_DIR)

    print("\n✅ Analysis complete.")
    print(f"   Figures saved in: {FIG_DIR.resolve()}")
    print("   Copy the printed tables (Markdown) into your report / slides.")
    print(f"   Table PNGs: table_cumulative_summary.png, table_year_summary_{KEY_YEAR}.png")

if __name__ == "__main__":
    main()

