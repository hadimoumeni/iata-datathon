import pandas as pd

# Anchors (percent, not fraction)

# S1 (policy-accelerated): ReFuelEU milestones and the brief's guidance to exceed from 2030
# Mandates: 2% (2025), 6% (2030), 20% (2035), 70% (2050)
# Brief indicates ~10–12% by 2030 and ~30% by 2035 for S1; we choose a central path:
S1_ANCHORS = {2025: 2.0, 2030: 11.0, 2035: 30.0, 2050: 70.0}

# S0 (BAU, no mandates): conservative, documented assumption
S0_ANCHORS = {2025: 1.0, 2030: 3.0, 2035: 10.0, 2050: 35.0}


def interp(anchors, years):
    xs = sorted(anchors)
    out = {}

    for i in range(len(xs)-1):
        y0, y1 = xs[i], xs[i+1]
        v0, v1 = anchors[y0], anchors[y1]
        steps = y1 - y0
        for k in range(steps+1):
            y = y0 + k
            frac = k/steps if steps else 0
            out[y] = v0 + frac*(v1 - v0)

    # clamp edges if needed
    for y in years:
        if y < xs[0]: out[y] = anchors[xs[0]]
        if y > xs[-1]: out[y] = anchors[xs[-1]]

    return [round(out[y], 1) for y in years]


years = list(range(2025, 2051))
df = pd.DataFrame({
    "year": years,
    "S0": interp(S0_ANCHORS, years),
    "S1": interp(S1_ANCHORS, years),
})

# basic checks
assert df["S0"].is_monotonic_increasing and df["S1"].is_monotonic_increasing
assert df[["S0","S1"]].min().min() >= 0 and df[["S0","S1"]].max().max() <= 100

out = "data/clean/saf_blend_targets__eu27__annual__2025-2050.csv"
df.to_csv(out, index=False)
print("Wrote", out)
print(df.head(8).to_string(index=False))
print("...")
print(df.tail(5).to_string(index=False))

