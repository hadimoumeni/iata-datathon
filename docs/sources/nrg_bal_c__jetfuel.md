# Eurostat – Jet fuel baseline (annual) → EU27 Mt

- **Dataset**: Eurostat Complete energy balances (`nrg_bal_c`)

- **Filters**: Domestic aviation (energy use) + International aviation (energy use); Kerosene‑type jet fuel; unit = ktoe; EU‑27 members summed

- **Conversion**: ktoe → GJ → MJ → tonnes → Mt (constants: `TOE_TO_GJ = 41.868`, `JET_NCV_MJ_PER_KG = 44.1`)

- **Check**: Latest year (2023) ≈ 42.2 Mt; aligns with datathon baseline guidance (~38–39 Mt for 2024/2025).

- **Use case**: Anchor for Obj‑1 total fuel computations.

