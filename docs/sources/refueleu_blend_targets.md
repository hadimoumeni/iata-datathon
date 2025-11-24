# SAF blending schedules (S0 & S1) — EU27 (2025–2050)

**Policy basis (S1)**: IE–IATA Datathon 2025 brief – ReFuelEU minimums: 2% (2025), 6% (2030), 20% (2035), 70% (2050). 

The brief also states S1 should exceed mandates from 2030 by ~5–10 pp (indicative ~10–12% by 2030; ~30% by 2035; 70% by 2050). 

We implement a central path: 2025=2%, 2030=11%, 2035=30%, 2050=70%, with piecewise-linear interpolation.

**BAU assumption (S0)**: No mandates; conservative adoption path with anchors 2025=1%, 2030=3%, 2035=10%, 2050=35%; 

linearly interpolated. This is a documented modelling assumption and can be tuned later. 

**Output**: `data/clean/saf_blend_targets__eu27__annual__2025-2050.csv` (columns: year, S0, S1; values are percentages).

**Notes**:

- Shares are EU27-wide; country splits not required for Obj‑1.

- Both series are monotonic and bounded [0,100].

- This file is a clean scenario input for Obj‑1 (SAF_Share by year), matching team requirements.

