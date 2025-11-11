"""
Reusable plotting functions for the IEU Sustainability Datathon.

This module provides standardized functions to create the primary visualizations
needed for the analysis and final presentation, ensuring a consistent style.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict

# ==============================================================================
# --- 1. PLOTTING STYLE & CONSTANTS ---
# Centralizing style choices makes it easy to maintain a consistent look.
# ==============================================================================

# Define a consistent color palette for the scenarios
SCENARIO_COLORS = {
    'S0': '#1f77b4',  # Muted Blue
    'S1': '#ff7f0e',  # Safety Orange
    'S2': '#2ca02c'   # Cooked Asparagus Green
}

# Standard figure size
DEFAULT_FIG_SIZE = (12, 7)

# Set a professional plot style
sns.set_theme(style="whitegrid")


# ==============================================================================
# --- 2. CORE VISUALIZATION FUNCTIONS ---
# ==============================================================================

def plot_scenario_comparison(
    scenario_results: Dict[str, pd.DataFrame],
    metric_to_plot: str,
    title: str,
    y_label: str,
    ax: plt.Axes = None,
    save_path: str = None
) -> None:
    """
    Plots a comparison of a single metric across multiple scenarios over time.

    Args:
        scenario_results (Dict[str, pd.DataFrame]): A dictionary where keys are scenario
                                                    names and values are the result DataFrames.
        metric_to_plot (str): The column name of the metric to plot from the DataFrames.
        title (str): The title for the chart.
        y_label (str): The label for the y-axis.
        ax (plt.Axes, optional): A matplotlib axes object to plot on. If None, a new
                                 figure and axes are created.
        save_path (str, optional): The file path to save the figure. If None, the
                                   plot is just shown.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=DEFAULT_FIG_SIZE)

    for name, df in scenario_results.items():
        if metric_to_plot in df.columns:
            ax.plot(df.index, df[metric_to_plot], label=name, color=SCENARIO_COLORS.get(name), linewidth=2.5)

    ax.set_title(title, fontsize=16, weight='bold')
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    ax.legend(title="Scenario", fontsize=10)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Improve readability of the y-axis
    if ax.get_ylim()[1] > 1000:
        ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)
    
    if ax is None:
        plt.show()


def plot_fuel_mix(
    scenario_df: pd.DataFrame,
    title: str,
    ax: plt.Axes = None,
    save_path: str = None
) -> None:
    """
    Creates a stacked area chart showing the fuel mix over time for a single scenario.

    Args:
        scenario_df (pd.DataFrame): The result DataFrame for a single scenario.
        title (str): The title for the chart.
        ax (plt.Axes, optional): A matplotlib axes object to plot on. If None, a new
                                 figure and axes are created.
        save_path (str, optional): The file path to save the figure.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=DEFAULT_FIG_SIZE)

    fuel_columns = ['Jet_Fuel_Volume_Mt', 'SAF_Volume_Mt']
    if not all(col in scenario_df.columns for col in fuel_columns):
        raise ValueError("DataFrame must contain 'Jet_Fuel_Volume_Mt' and 'SAF_Volume_Mt' columns.")

    ax.stackplot(
        scenario_df.index,
        scenario_df['Jet_Fuel_Volume_Mt'],
        scenario_df['SAF_Volume_Mt'],
        labels=['Conventional Jet Fuel', 'Sustainable Aviation Fuel (SAF)'],
        colors=['#6c757d', '#2ca02c'], # Gray and Green
        alpha=0.8
    )

    ax.set_title(title, fontsize=16, weight='bold')
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Fuel Volume (Mt)", fontsize=12)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.set_xlim(scenario_df.index.min(), scenario_df.index.max())

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)

    if ax is None:
        plt.show()


def plot_correlation_heatmap(
    df: pd.DataFrame,
    title: str = "Correlation Matrix of Key Metrics",
    save_path: str = None
) -> None:
    """
    Plots a heatmap of the correlation matrix for a given DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to analyze.
        title (str): The title for the heatmap.
        save_path (str, optional): The file path to save the figure.
    """
    plt.figure(figsize=(10, 8))
    corr = df.corr()
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap='coolwarm',
        linewidths=.5
    )
    plt.title(title, fontsize=16, weight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)
    
    plt.show()


# ==============================================================================
# --- 3. EXAMPLE USAGE BLOCK ---
# This allows the script to be run directly to test the functions.
# ==============================================================================
if __name__ == '__main__':
    # --- Create Sample Data for Demonstration ---
    from src.modeling import calculate_fuel_demand, run_scenario_analysis

    BASE_DEMAND = 80.0
    TRAFFIC_GROWTH = 0.025
    
    base_fuel_demand = calculate_fuel_demand(BASE_DEMAND, TRAFFIC_GROWTH)
    ops_efficient_fuel_demand = calculate_fuel_demand(BASE_DEMAND, TRAFFIC_GROWTH, apply_operational_gains=True)

    s0_results = run_scenario_analysis(base_fuel_demand, 'S0')
    s1_results = run_scenario_analysis(base_fuel_demand, 'S1')
    s2_results = run_scenario_analysis(ops_efficient_fuel_demand, 'S2')

    all_scenarios = {'S0': s0_results, 'S1': s1_results, 'S2': s2_results}

    print("--- Generating Example Plots ---")

    # --- Example 1: Plotting Scenario Comparison for CO2 Emissions ---
    plot_scenario_comparison(
        scenario_results=all_scenarios,
        metric_to_plot='CO2_Emissions_Generated_Mt',
        title='EU27 Aviation CO₂ Emissions by Scenario (2025-2050)',
        y_label='CO₂ Emissions (Mt)'
    )

    # --- Example 2: Plotting the Fuel Mix for the S2 Scenario ---
    plot_fuel_mix(
        scenario_df=s2_results,
        title='Fuel Mix Evolution for S2: Accelerated Abatement Scenario'
    )
    
    # --- Example 3: Plotting a Correlation Heatmap for S1 results ---
    # Select a subset of columns for a cleaner heatmap
    s1_subset_for_corr = s1_results[[
        'Total_Fuel_Demand_Mt',
        'SAF_Blending_Share_%',
        'CO2_Emissions_Generated_Mt',
        'Total_Fuel_Cost_EUR_Bn',
        'Carbon_Cost_EUR_Bn',
        'Total_Cost_of_Compliance_EUR_Bn'
    ]]
    plot_correlation_heatmap(s1_subset_for_corr, title="Correlation Matrix for S1 Scenario")

    print("\n--- Plotting Demo Complete ---")
