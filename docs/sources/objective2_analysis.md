# Objective 2 – Scenario Comparison & Visualization

This document describes what `objective2_analysis.py` does and how to use it to
demonstrate that **S2 (Smart Levy)** is economically preferable to S1 (pure
mandate), while achieving the same emissions reductions.

---

## 1. Inputs & Assumptions

The script expects the following file to exist (already produced by
`objective2_calc.py`):

- `data/metrics/obj2_economic_results.csv`

This CSV must contain the columns created by the updated `objective2_calc.py`,
including at least:

- **Scenario 0 (BAU)**:
  - `S0_Total_Cost_Bn`, `S0_Fuel_Cost_Bn`, `S0_Carbon_Cost_Bn`
  - `S0_CO2_Emissions_Mt`

- **Scenario 1 (Mandate)**:
  - `S1_Total_Cost_Bn`, `S1_Total_Fuel_Cost_Bn`, `S1_SAF_Cost_Bn`,
    `S1_Jet_Cost_Bn`, `S1_Carbon_Cost_Bn`, `S1_Logistics_Penalty_Bn`
  - `S1_CO2_Emissions_Mt`, `CO2_Avoided_Mt`,
    `Cost_per_tCO2_Abated_USD`
  - `S1_SAF_Vol_Mt`, `S1_Vol_HEFA_Mt`, `S1_Vol_PtL_Mt`,
    `HEFA_EU_Supply_Cap_Mt`
  - `S1_Realised_SAF_Price_USD_per_t`
  - `S1_Logistics_Emissions_Mt`, `S1_Logistics_Carbon_Cost_Bn`

- **Scenario 2 (Smart Levy, built on S1 volumes)**:
  - `S2_Total_Cost_Bn`
  - `S2_Total_Cost_Incl_Levy_Bn`
  - `S2_Levy_Annual_Revenue_Bn`, `S2_SAF_Subsidy_Pool_Bn`
  - `S2_Effective_SAF_Price_USD_per_t`
  - `S2_Total_Fuel_Cost_Bn`, `S2_SAF_Cost_Bn`, `S2_Jet_Cost_Bn`
  - `S2_Carbon_Cost_Bn`, `S2_Logistics_Penalty_Bn`
  - `S2_Cost_per_tCO2_Abated_USD`

The economic and Smart Levy assumptions (levy per passenger, passengers per
year, logistics_tkm_per_tonne, HEFA global cap, etc.) are documented in:

- `docs/references/economic_sources.yaml`

---

## 2. What the Script Produces

Running:

```bash
python etl/objective2_analysis.py
```

will:

1. **Load** `data/metrics/obj2_economic_results.csv`.

2. **Compute and print summary tables to console** (as Markdown if possible):
   - **Cumulative 2026–2050 scenario comparison** — Shows total costs, emissions, green premiums, and cost efficiency metrics across all scenarios.
   - **One-year snapshot (by default 2030)** — Shows cost breakdown, emissions, and SAF prices for a specific year.
   
   **💡 Tip**: The tables are printed to the console in Markdown format (if `tabulate` is installed) or plain text. You can **copy-paste them directly** into your report or slides. They're perfect for:
   - Sanity-checking the model
   - Showing "S2 beats S1" at a glance
   - Including in presentations without manual formatting

3. **Generate and save plots** (PNG files) into the `figures/` directory:
   - `total_costs_scenario_comparison.png`
   - `cost_breakdown_2030.png`
   - `cost_per_tco2_s1_vs_s2.png`
   - `saf_vs_jet_prices.png`
   - `feedstock_wall_hefa_ptl.png`

**All outputs are ready to drop into the slide deck or report.**

---

## 3. Summary Tables Explained

The script prints two summary tables to the console that you can copy-paste directly into your report or slides. These tables are **not saved as files** — they're printed to stdout for easy copy-pasting.

### Cumulative Summary (2026–2050)

This table aggregates all costs, emissions, and metrics across the full
modelling horizon (2026–2050). Key insights:

- **Total_Cost_Bn**: Cumulative total cost for each scenario (airline perspective).
- **Total_Cost_Incl_Levy_Bn**: For S2, includes passenger levy burden (system-wide view).
- **Green_Premium_vs_S0_Bn**: Extra cost vs BAU (S0).
- **Total_CO2_Avoided_vs_S0_Mt**: Total emissions reductions (same for S1 & S2).
- **Cost_per_tCO2_Abated_USD**: Efficiency metric — lower is better.
- **Total_Levy_Revenue_Bn**: Total passenger levy collected (S2 only).
- **Avg_SAF_Price_USD_per_t**: Average SAF price paid by airlines.

**Expected result**: S2 should show lower `Total_Cost_Bn` than S1 (airline
perspective), but similar or better `Cost_per_tCO2_Abated_USD`, demonstrating
that the Smart Levy makes decarbonization more affordable.

### Year Summary (2030)

This table breaks down costs and emissions for a single "story year" (2030 by
default, configurable via `KEY_YEAR`). It shows:

- **Cost components**: Fuel, Carbon, Logistics, Levy (system view).
- **Emissions**: CO2 emitted and avoided vs S0.
- **SAF prices**: What airlines actually pay per tonne of SAF.

Use this to explain the cost structure at a specific point in time, e.g., when
the feedstock wall is first hit (2031 in our model).

---

## 4. Plots Explained

### 1. Total Costs Scenario Comparison

**File**: `total_costs_scenario_comparison.png`

**What it shows**: Line plot of annual total cost (airline perspective) for S0,
S1, and S2 over 2026–2050.

**Key message**: S2 costs less than S1 for airlines, while achieving the same
emissions reductions.

### 2. Cost Breakdown (2030)

**File**: `cost_breakdown_2030.png`

**What it shows**: Stacked bar chart showing fuel, carbon, logistics, and levy
costs for each scenario in 2030.

**Key message**: Visual breakdown of where costs come from. S2's levy is shown
as a passenger burden (not an airline cost), while S1's logistics penalty is
pure waste.

### 3. Cost per tCO2 Abated

**File**: `cost_per_tco2_s1_vs_s2.png`

**What it shows**: Line plot comparing the cost efficiency of emissions
reductions (USD per tonne CO2 avoided) for S1 vs S2.

**Key message**: S2 is more cost-efficient — it achieves the same reductions
at lower cost per tonne.

### 4. SAF vs Jet A-1 Prices

**File**: `saf_vs_jet_prices.png`

**What it shows**: Line plot of Jet A-1 list price, S1 blended SAF price
(HEFA+PtL), and S2 effective SAF price (after subsidies).

**Key message**: S2 subsidies bring SAF prices closer to Jet A-1, making
decarbonization more affordable.

### 5. Feedstock Wall (HEFA vs PtL)

**File**: `feedstock_wall_hefa_ptl.png`

**What it shows**: Stacked area plot of HEFA and PtL SAF volumes, with the
HEFA EU supply cap (5.0 Mt) shown as a dashed line.

**Key message**: When SAF demand exceeds the HEFA cap (2031), expensive PtL
must fill the gap, driving up costs in S1. S2's subsidies help offset this.

---

## 5. Customization

### Change the Key Year

Edit `KEY_YEAR` in `objective2_analysis.py`:

```python
KEY_YEAR = 2035  # or any year in 2026-2050
```

This affects:
- The year summary table
- The cost breakdown plot filename

### Change Output Directory

Edit `FIG_DIR`:

```python
FIG_DIR = Path("outputs/figures")  # or any path
```

---

## 6. Dependencies

- `pandas` (data loading and manipulation)
- `numpy` (numerical operations)
- `matplotlib` (plotting)
- Optional: `tabulate` (for prettier Markdown table output)

Install with:

```bash
pip install pandas numpy matplotlib tabulate
```

---

## 7. Integration with Pipeline

This script is the final step in the Objective 2 pipeline:

1. **`etl/compute_obj1.py`** → Produces `obj1_official_output__eu27__annual__2026-2050.csv`
2. **`etl/objective2_calc.py`** → Produces `obj2_economic_results.csv`
3. **`etl/objective2_analysis.py`** → Produces summary tables and figures

Run the full pipeline:

```bash
python etl/compute_obj1.py
python etl/objective2_calc.py
python etl/objective2_analysis.py
```

---

## 8. Expected Results

After running the script, you should see:

- **Console output**: Two summary tables (cumulative and year-specific)
- **`figures/` directory**: Five PNG files ready for slides/reports
- **Key insight**: S2 (Smart Levy) shows lower airline costs than S1, with
  the same emissions reductions, demonstrating the economic advantage of the
  Smart Levy approach.

