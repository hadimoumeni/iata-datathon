"""
Reads clean inputs from /data/clean and writes the judge-required Obj-1 table.

Complete the TODOs after Step 2–4.
"""
import pandas as pd

EF = 3.16  # tCO2/t fuel (use consistently)


traffic = pd.read_csv("data/clean/traffic_projection__eu27__annual__2025-2050.csv")
blend   = pd.read_csv("data/clean/saf_blend_targets__eu27__annual__2025-2050.csv")
base    = pd.read_csv("data/clean/jet_fuel_baseline__eu27__annual__1990-2025_mt.csv")
prices  = pd.read_csv("data/clean/price_inputs__eu__annual__2025-2050.csv")  # optional for Obj-1


# TODO: compute scale so 2025 total_fuel_mt matches baseline (~38-39 Mt).
# TODO: split into jet_mt / saf_mt using S0 or S1 share.
# TODO: CO2_generated = jet_mt*EF + saf_mt*EF*(1 - saf_lca_reduction_pct/100)
# TODO: Avoided_CO2 = total_mt*EF - CO2_generated
# TODO: write data/clean/obj1_required_output__eu27__annual__2026-2050.csv

