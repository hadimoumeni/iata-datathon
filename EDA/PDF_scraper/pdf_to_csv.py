#!/usr/bin/env python3
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
    parser = argparse.ArgumentParser(description="Extract tables from a PDF or directory (tabula-py) and save as CSV(s).")
    parser.add_argument("path", type=Path, help="Input PDF file or directory containing PDFs (will ignore other files)")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output CSV file or output directory. When input is a directory, this should be a directory.")
    parser.add_argument("--pages", default="all", help="Pages to parse (e.g. '1', '1-3', 'all'). Default: all")
    parser.add_argument("--lattice", action="store_true", help="Use lattice mode (good for tables with visible lines)")
    parser.add_argument("--guess", dest="guess", action="store_true", default=True, help="Let tabula guess table areas (default)")
    parser.add_argument("--no-guess", dest="guess", action="store_false", help="Disable guessing of table areas")
    parser.add_argument("--single", action="store_true", help="Merge all found tables per-PDF into a single CSV (may produce uneven columns)")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursively search directories for PDFs")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args(argv)
    input_path = args.path

    if not input_path.exists():
        print(f"ERROR: input path not found: {input_path}")
        return 2

    # If tabula-py not available, bail early with a helpful message
    if tabula is None:
        print("ERROR: tabula-py unavailable. Please install the Python dependency (see requirements.txt).", file=sys.stderr)
        print("tabula-py requires Java (tabula-java). Make sure Java is installed and on PATH (java -version).", file=sys.stderr)
        return 3

    if not check_java():
        print("WARNING: Java doesn't seem to be available on PATH. tabula-py may fail. Ensure Java is installed and 'java' is on your PATH.")

    # Build list of PDF files to process
    pdf_files: List[Path] = []
    if input_path.is_file():
        if input_path.suffix.lower() == ".pdf":
            pdf_files = [input_path]
        else:
            print(f"ERROR: given file is not a PDF: {input_path}")
            return 2
    else:
        # directory: find PDFs (non-recursive by default)
        if args.recursive:
            pdf_files = [p for p in input_path.rglob("*.pdf") if p.is_file()]
        else:
            pdf_files = [p for p in input_path.glob("*.pdf") if p.is_file()]

    if not pdf_files:
        print(f"No PDF files found under: {input_path}")
        return 0

    # Determine output behavior
    out_arg = args.output
    multiple_inputs = len(pdf_files) > 1

    # default clean_data directory in repo root (current working dir)
    repo_clean_dir = Path.cwd() / "clean_data"
    written_all: List[Path] = []

    for pdf in sorted(pdf_files):
        # Choose output path per PDF
        if out_arg:
            # If output arg is a directory or multiple inputs, ensure directory
            if multiple_inputs or (out_arg.exists() and out_arg.is_dir()):
                out_dir = out_arg
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{pdf.stem}.csv"
            else:
                # Single input and output points to a file path (may not exist yet)
                out_path = out_arg
        else:
            # No output provided: send outputs into repo's clean_data folder
            repo_clean_dir.mkdir(parents=True, exist_ok=True)
            out_path = repo_clean_dir / f"{pdf.stem}.csv"

        if args.verbose:
            print(f"Processing: {pdf} -> {out_path}")

        try:
            dfs = extract_with_tabula(pdf, pages=args.pages, lattice=args.lattice, guess=args.guess)
        except Exception as e:
            print(f"Failed to extract tables from {pdf}: {e}", file=sys.stderr)
            continue

        if not dfs:
            if args.verbose:
                print(f"No tables found in {pdf}")
            continue

        written = write_tables(dfs, out_path, single=args.single)
        written_all.extend(written)

    if args.verbose:
        print(f"Wrote {len(written_all)} CSV file(s)")
        for p in written_all:
            print(" -", p)
    elif written_all:
        print(str(written_all[0]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
