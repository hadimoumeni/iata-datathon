import pandas as pd
import math
from pathlib import Path

# ---- Inputs (edit if your filenames differ) -------------------------------
TRAFFIC_CSV = Path("data/clean/traffic_projection__eu27__annual__2025-2050.csv")
BLEND_CSV   = Path("data/clean/saf_blend_targets__eu27__annual__2025-2050.csv")
BASELINE_CSV= Path("data/clean/jet_fuel_baseline__eu27__annual__1990-LATEST_mt.csv")

# ---- Output ---------------------------------------------------------------
OUT_CSV     = Path("data/metrics/obj1_official_output__eu27__annual__2026-2050.csv")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# ---- Assumptions (documented in references/assumptions.yaml) --------------
# Fossil jet emission factor (tCO2 per tonne fuel)
EF_TCO2_PER_T = 3.16     # use consistently; brief allows reasonable assumptions if documented
# Central SAF lifecycle reduction vs fossil (percentage points)
SAF_LCA_REDUCTION_PCT = 75.0

# Recommended baseline from the brief: ~38–39 Mt total fuel (EU27) in 2024/2025.
# We'll target 38.5 Mt unless your baseline CSV includes 2025 explicitly.
RECOMMENDED_BASELINE_2025_MT = 38.5  # edit if you want 38.0 or 39.0

# ---- Load inputs ----------------------------------------------------------
traffic = pd.read_csv(TRAFFIC_CSV)            # columns: year, traffic_index_2025=100
blend   = pd.read_csv(BLEND_CSV)              # columns: year, S0, S1
base    = pd.read_csv(BASELINE_CSV)           # columns: year, jet_fuel_mt

# Ensure integer years
for df in (traffic, blend, base):
    df['year'] = df['year'].astype(int)

# Determine baseline_2025 (Mt)
if (base['year'] == 2025).any():
    baseline_2025_mt = float(base.loc[base['year']==2025, 'jet_fuel_mt'].iloc[0])
else:
    baseline_2025_mt = RECOMMENDED_BASELINE_2025_MT

# Scale traffic index to Mt so that 2025 hits the baseline
# total_fuel_mt(y) = baseline_2025_mt * (index(y) / index(2025))
idx_2025 = float(traffic.loc[traffic['year']==2025, 'traffic_index_2025=100'].iloc[0])
if idx_2025 == 0 or math.isnan(idx_2025):
    raise ValueError("traffic index for 2025 is missing or zero.")

combined = traffic.merge(blend, on='year', how='left')

# Fill missing traffic index values (forward projection)
# Simple assumption: constant growth from last known value, or flat if only 2025 exists
traffic_known = combined[combined['traffic_index_2025=100'].notna()].copy()
if len(traffic_known) > 1:
    # If we have historical data, use last known growth rate
    last_idx = traffic_known['traffic_index_2025=100'].iloc[-1]
    prev_idx = traffic_known['traffic_index_2025=100'].iloc[-2]
    growth_rate = (last_idx / prev_idx) ** (1.0 / (traffic_known['year'].iloc[-1] - traffic_known['year'].iloc[-2]))
    # Project forward
    for year in range(2026, 2051):
        if pd.isna(combined.loc[combined['year']==year, 'traffic_index_2025=100'].values[0]):
            years_ahead = year - traffic_known['year'].iloc[-1]
            combined.loc[combined['year']==year, 'traffic_index_2025=100'] = last_idx * (growth_rate ** years_ahead)
else:
    # If only 2025 exists, assume flat traffic (index stays at 100)
    combined['traffic_index_2025=100'] = combined['traffic_index_2025=100'].fillna(100.0)

combined['total_fuel_mt'] = baseline_2025_mt * (combined['traffic_index_2025=100'] / idx_2025)

# Helper to compute metrics for a scenario column ('S0' or 'S1')
def compute_for_scenario(df, scen_col, scen_id, ef=EF_TCO2_PER_T, saf_red=SAF_LCA_REDUCTION_PCT):
    out = df[['year','total_fuel_mt',scen_col]].copy()
    out.rename(columns={scen_col:'saf_share_pct'}, inplace=True)
    # shares are in %, convert to fraction
    frac = out['saf_share_pct'] / 100.0
    out['saf_mt'] = out['total_fuel_mt'] * frac
    out['jet_mt'] = out['total_fuel_mt'] - out['saf_mt']
    # CO2 generated = jet*EF + saf*EF*(1 - LCA_reduction)
    out['co2_generated_mt'] = out['jet_mt']*ef + out['saf_mt']*ef*(1.0 - saf_red/100.0)
    # Avoided CO2 = baseline(0% SAF) - generated
    out['co2_avoided_mt'] = out['total_fuel_mt']*ef - out['co2_generated_mt']
    # Assemble judge schema; filter to 2026–2050 per spec
    o = out[(out['year']>=2026) & (out['year']<=2050)][
        ['year','total_fuel_mt','saf_share_pct','co2_generated_mt','co2_avoided_mt']
    ].copy()
    o.insert(1, 'Scenario', scen_id)
    o.rename(columns={
        'year':'Year',
        'total_fuel_mt':'Total_Fuel',
        'saf_share_pct':'SAF_Share',
        'co2_generated_mt':'CO2_Emissions',
        'co2_avoided_mt':'Avoided_CO2'
    }, inplace=True)
    # Optional rounding for readability (not required by spec)
    for c in ['Total_Fuel','SAF_Share','CO2_Emissions','Avoided_CO2']:
        o[c] = o[c].astype(float).round(3)
    return o

res0 = compute_for_scenario(combined, 'S0', 0)
res1 = compute_for_scenario(combined, 'S1', 1)
final = pd.concat([res0, res1], ignore_index=True).sort_values(['Year','Scenario'])

# Validate schema & ranges
required_cols = ['Year','Scenario','Total_Fuel','SAF_Share','CO2_Emissions','Avoided_CO2']
assert list(final.columns) == required_cols, f"Schema mismatch: {final.columns}"
assert final['Year'].min()==2026 and final['Year'].max()==2050, "Year range must be 2026–2050"

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
final.to_csv(OUT_CSV, index=False)

print("Wrote:", OUT_CSV)
print(final.head(6).to_string(index=False))
print("...")
print(final.tail(6).to_string(index=False))
