# SAF Blending Targets (EU27, 2025-2050)

- **Dataset**: `saf_blend_targets__eu27__annual__2025-2050.csv`

- **Method**: Generated via `etl/make_saf_blend_targets.py` using piecewise-linear interpolation. S1: 2025=2%, 2030=11%, 2035=30%, 2050=70%. S0: 2025=1%, 2030=3%, 2035=10%, 2050=35%.

- **Use case**: Driver for S0/S1 Scenario Modelling in Objective 1.

- **Note**: Both series monotonic [0,100]. S1 exceeds ReFuelEU minimums from 2030.

