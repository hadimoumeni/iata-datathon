#!/usr/bin/env python3
"""
Simple PDF table scraper using tabula-py.

This script extracts tables from a PDF and writes them to one or more CSV files.

Notes:
- Requires Java installed and available on PATH (tabula-py uses tabula-java).
- Install Python deps with: pip install -r requirements.txt
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import List

import pandas as pd

try:
    import tabula
except Exception as e:  # pragma: no cover - runtime environment dependent
    tabula = None


def extract_with_tabula(pdf: Path, pages: str = "all", lattice: bool = False, guess: bool = True) -> List[pd.DataFrame]:
    if tabula is None:
        raise RuntimeError("tabula-py is not installed or failed to import")
    # tabula.read_pdf returns a list of DataFrames when multiple_tables=True
    dfs = tabula.read_pdf(str(pdf), pages=pages, lattice=lattice, guess=guess, multiple_tables=True)
    # tabula may return a single DataFrame or list
    if isinstance(dfs, pd.DataFrame):
        return [dfs]
    return list(dfs)


def write_tables(dfs: List[pd.DataFrame], output: Path, single: bool = False) -> List[Path]:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []
    if single:
        # Attempt to concatenate tables vertically. If columns mismatch, pandas will fill NaNs.
        try:
            out_df = pd.concat(dfs, ignore_index=True, sort=False)
        except Exception:
            out_df = dfs[0] if dfs else pd.DataFrame()
        out_df.to_csv(output, index=False)
        written.append(output)
        return written

    # If there's only one table, write it to the given output path
    if len(dfs) == 1:
        dfs[0].to_csv(output, index=False)
        written.append(output)
        return written

    # Multiple tables -> write separate files with suffix
    stem = output.stem
    parent = output.parent
    for i, df in enumerate(dfs, start=1):
        out_path = parent / f"{stem}_table{i}.csv"
        df.to_csv(out_path, index=False)
        written.append(out_path)
    return written


def check_java():
    # quick check: try to run tabula.environment_info if available, otherwise rely on tabula.read_pdf errors
    try:
        import subprocess

        p = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if p.returncode != 0:
            return False
        return True
    except Exception:
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract tables from a PDF using tabula-py and save as CSV(s).")
    parser.add_argument("pdf", type=Path, help="Input PDF file path")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output CSV file or directory (if not provided, uses PDF basename)")
    parser.add_argument("--pages", default="all", help="Pages to parse (e.g. '1', '1-3', 'all'). Default: all")
    parser.add_argument("--lattice", action="store_true", help="Use lattice mode (good for tables with visible lines)")
    parser.add_argument("--guess", dest="guess", action="store_true", default=True, help="Let tabula guess table areas (default)")
    parser.add_argument("--no-guess", dest="guess", action="store_false", help="Disable guessing of table areas")
    parser.add_argument("--single", action="store_true", help="Merge all found tables into a single CSV (may produce uneven columns)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args(argv)
    pdf = args.pdf
    if not pdf.exists():
        print(f"ERROR: PDF not found: {pdf}")
        return 2

    default_out = pdf.with_suffix(".csv")
    output = args.output or default_out

    if tabula is None:
        print("ERROR: tabula-py unavailable. Please install the Python dependency (see requirements.txt).", file=sys.stderr)
        print("tabula-py requires Java (tabula-java). Make sure Java is installed and on PATH (java -version).", file=sys.stderr)
        return 3

    if not check_java():
        print("WARNING: Java doesn't seem to be available on PATH. tabula-py may fail. Ensure Java is installed and 'java' is on your PATH.")

    try:
        dfs = extract_with_tabula(pdf, pages=args.pages, lattice=args.lattice, guess=args.guess)
    except Exception as e:
        print("Failed to extract tables with tabula-py:", e, file=sys.stderr)
        return 4

    if not dfs:
        print("No tables found in PDF.")
        return 0

    written = write_tables(dfs, output, single=args.single)

    if args.verbose:
        print(f"Wrote {len(written)} CSV file(s):")
        for p in written:
            print(" -", p)
    else:
        print(str(written[0]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
