# Objective 2: Economic Results & TCO Analysis

- **Dataset**: `obj2_economic_results.csv`

- **Method**: Generated via `etl/objective2_calc.py` combining Obj1 output (`obj1_official_output__eu27__annual__2026-2050.csv`) with economic assumptions (`layer3_economic_assumptions.csv`). 

  **S0 (Business as Usual)**: Total cost = (Total_Fuel_Mt × Price_JetA1_USD) + (CO2_Emissions_Mt × ETS_Paying_Ratio × Carbon_Price_USD). Assumes minimal SAF uptake, priced at baseline Jet A-1 rates. ETS paying ratio: 0.5 in 2025, 1.0 from 2026+ (free allowances phase out).

  **S1 (Policy Mandate)**: Total cost = Jet A-1 cost + SAF cost (blended) + Carbon cost + Logistics penalty. SAF volumes split between HEFA and PtL based on Feedstock Wall: if SAF demand ≤ 5.0 Mt, all priced at HEFA ($2,200→$1,850/t); if demand > 5.0 Mt, excess priced at PtL ($3,800→$1,200/t). Logistics penalty: $150/t applied to all SAF volumes (represents decentralized trucking costs in S1).

  **Green Premium**: Calculated as S1_Total_Cost_Bn - S0_Total_Cost_Bn, representing the additional cost of policy-accelerated decarbonization vs. business-as-usual.

- **Use case**: Final financial evidence comparing Scenario 0 vs Scenario 1 total cost of ownership (TCO). Quantifies inefficiency of current system through Logistics Penalty ($53B cumulative 2026-2050) and demonstrates Feedstock Wall constraint impact (wall hit in 2031 when SAF demand exceeds HEFA supply cap). Key metrics for presentation: cumulative costs, green premium, logistics savings opportunity.

- **Note**: Logistics penalty $150/t applied to all S1 SAF volumes (represents cost differential between decentralized trucking vs. centralized pipelines). Free allowances drop to 0% after 2026 (ETS_Paying_Ratio = 1.0). Wall_Hit boolean flag indicates when HEFA cap (5.0 Mt) is exceeded (starts 2031). All costs in billions USD. SAF_Share converted from percentage to fraction for volume calculations.

