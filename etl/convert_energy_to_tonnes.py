import pandas as pd
from pathlib import Path

RAW = "data/raw/eurostat/nrg_bal_c__<YYYYMMDD>.csv"
OUT = "data/clean/jet_fuel_baseline__eu27__annual__1990-LATEST_mt.csv"

EU27 = {
    "AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","HU","IE",
    "IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"
}

# conversion constants (also in references/assumptions.yaml)
TOE_TO_GJ = 41.868
JET_NCV_MJ_PER_KG = 44.1  # MJ/kg
KG_PER_T = 1000


def ktoe_to_mt_jet(ktoe: float) -> float:
    gj = ktoe * 1_000 * TOE_TO_GJ   # ktoe -> toe -> GJ
    mj = gj * 1_000                 # GJ -> MJ
    tonnes = mj / (JET_NCV_MJ_PER_KG * KG_PER_T)  # MJ / (MJ/t)
    return tonnes / 1e6             # t -> Mt


def main():
    df = pd.read_csv(RAW)

    # Normalise column names seen in Eurostat "linear" exports
    cols = {c.lower(): c for c in df.columns}
    time_col = cols.get("time_period") or cols.get("time")
    val_col  = cols.get("obs_value") or cols.get("values") or cols.get("value")
    geo_col  = cols.get("geo")
    unit_col = cols.get("unit")
    nrg_col  = cols.get("nrg_bal")
    siec_col = cols.get("siec")

    # Keep aviation final-consumption (domestic + international)
    def is_domestic_avi(s: str) -> bool:
        s = (s or "").lower()
        return "domestic aviation" in s or "fc_tra_davi_e" in s.lower()

    def is_international_avi(s: str) -> bool:
        s = (s or "").lower()
        return "international aviation" in s or "intavi" in s.lower()

    def is_kerosene(s: str) -> bool:
        return "kerosene-type jet fuel" in (s or "").lower()

    d = df[[geo_col, time_col, val_col, unit_col, nrg_col, siec_col]].copy()
    d = d.rename(columns={geo_col:"geo", time_col:"year", val_col:"ktoe",
                          unit_col:"unit", nrg_col:"nrg_bal", siec_col:"siec"})
    d["year"] = d["year"].astype(str).str[:4].astype(int)

    # Filter: unit, kerosene jet fuel, and the two aviation items
    d = d[d["unit"].str.contains("Thousand tonnes of oil equivalent", case=False, na=False)]
    d = d[d["siec"].apply(is_kerosene)]
    d = d[d["nrg_bal"].apply(lambda s: is_domestic_avi(s) or is_international_avi(s))]

    # EU27 aggregate = sum of member states; if only EU27 total present, use it
    members = d[d["geo"].isin(EU27)]
    if members.empty:
        eu = d[d["geo"].str.contains("European Union - 27", na=False)]
    else:
        eu = members

    yearly_ktoe = eu.groupby("year", as_index=False)["ktoe"].sum()
    yearly_ktoe["jet_fuel_mt"] = yearly_ktoe["ktoe"].apply(ktoe_to_mt_jet)

    out = yearly_ktoe[["year","jet_fuel_mt"]].sort_values("year")
    out.to_csv(OUT, index=False)
    print(f"Wrote {OUT}")
    print("Years:", out["year"].min(), "→", out["year"].max())
    print(out.tail(3))


if __name__ == "__main__":
    main()
