import pandas as pd

INPATH = "data/raw/eurostat/avia_tf_cm__<YYYYMMDD>.csv"
OUT    = "data/clean/traffic_projection__eu27__annual__2025-2050.csv"

EU27 = {
    "AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","HU","IE",
    "IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"
}


def main():
    df = pd.read_csv(INPATH)
    cols = {c.lower(): c for c in df.columns}
    time_col = cols.get("time_period") or cols.get("time")
    val_col  = cols.get("obs_value") or cols.get("values") or cols.get("value")
    geo_col  = cols.get("geo")

    d = df[[geo_col, time_col, val_col]].rename(columns={geo_col:"geo", time_col:"time", val_col:"flights"})
    d["year"] = d["time"].astype(str).str[:4].astype(int)

    # Prefer summing members to avoid non-EU27 noise
    members = d[d["geo"].isin(EU27)]
    if members.empty:
        eu = d[d["geo"].str.contains("EU27|27 countries", case=False, na=False)]
    else:
        eu = members

    annual = eu.groupby("year", as_index=False)["flights"].sum()

    # Base on 2025 if present, else use the latest full year and rescale later
    if (annual["year"] == 2025).any():
        base = float(annual.loc[annual["year"] == 2025, "flights"].iloc[0])
    else:
        # pick latest year as temporary base
        base = float(annual.sort_values("year")["flights"].iloc[-1])

    annual["traffic_index_2025=100"] = (annual["flights"] / base) * 100
    out = pd.DataFrame({"year": list(range(2025, 2051))}).merge(
        annual[["year","traffic_index_2025=100"]], on="year", how="left"
    )
    out.to_csv(OUT, index=False)
    print(f"Wrote {OUT}")
    print(out.head(), "\n...\n", out.tail())


if __name__ == "__main__":
    main()
