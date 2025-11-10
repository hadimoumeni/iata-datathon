#!/usr/bin/env python3
"""
Filter CSV files to only include rows for European Union member countries.

Usage examples:
  python EDA/filter_eu.py data/annual-co-emissions.csv
  python EDA/filter_eu.py data/ -o clean_data/ -r

Default behaviour: when given a directory, will process all `.csv` files in it (non-recursive)
and write outputs to `clean_data/<original_stem>_eu.csv` unless `-o` is provided.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import pandas as pd


EU_COUNTRIES = {
    # Official/commonly used English names (as of 2025, 27 members)
    "Austria",
    "Belgium",
    "Bulgaria",
    "Croatia",
    "Cyprus",
    "Czechia",
    "Czech Republic",
    "Denmark",
    "Estonia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hungary",
    "Ireland",
    "Italy",
    "Latvia",
    "Lithuania",
    "Luxembourg",
    "Malta",
    "Netherlands",
    "Poland",
    "Portugal",
    "Romania",
    "Slovakia",
    "Slovenia",
    "Spain",
    "Sweden",
}


def filter_df_eu(df: pd.DataFrame, entity_col: str = "Entity") -> pd.DataFrame:
    if entity_col not in df.columns:
        raise ValueError(f"Column '{entity_col}' not found in DataFrame")
    # Some files may have leading/trailing whitespace in names -> normalize
    names = df[entity_col].astype(str).str.strip()
    mask = names.isin(EU_COUNTRIES)
    return df[mask].copy()


def csv_files_in(path: Path, recursive: bool = False) -> List[Path]:
    if path.is_file():
        return [path]
    if recursive:
        return [p for p in path.rglob("*.csv") if p.is_file()]
    return [p for p in path.glob("*.csv") if p.is_file()]


def process_file(inp: Path, out_dir: Path, entity_col: str = "Entity") -> Path | None:
    try:
        df = pd.read_csv(inp)
    except Exception as e:
        print(f"Skipping {inp} — failed to read CSV: {e}")
        return None

    try:
        df_eu = filter_df_eu(df, entity_col=entity_col)
    except ValueError as e:
        print(f"Skipping {inp} — {e}")
        return None

    if df_eu.empty:
        print(f"No EU rows found in {inp}; skipping output.")
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{inp.stem}_eu.csv"
    df_eu.to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(df_eu)} rows)")
    return out_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Filter CSV(s) to EU countries only")
    parser.add_argument("input", type=Path, help="Input CSV file or directory containing CSVs")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output directory (default: clean_data)")
    parser.add_argument("--entity-col", default="Entity", help="Name of the column containing country/entity names (default: Entity)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively search directories for CSV files")

    args = parser.parse_args(list(argv) if argv is not None else None)
    inp = args.input
    out_dir = args.output or (Path.cwd() / "clean_data")

    files = csv_files_in(inp, recursive=args.recursive)
    if not files:
        print(f"No CSV files found in {inp}")
        return 0

    written = []
    for f in sorted(files):
        # skip files already in the output dir to avoid reprocessing
        try:
            if f.resolve().parent == out_dir.resolve():
                continue
        except Exception:
            pass
        res = process_file(f, out_dir, entity_col=args.entity_col)
        if res:
            written.append(res)

    print(f"Completed — wrote {len(written)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
