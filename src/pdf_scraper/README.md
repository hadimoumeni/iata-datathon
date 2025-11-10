# PDF scraper (tabula-py)

This folder contains a small utility to extract tabular data from PDF files using `tabula-py` and save the results as CSV file(s).

Files
- `pdf_to_csv.py` - CLI script that uses tabula-py to extract tables and write CSV(s).
- `requirements.txt` - Python dependencies.

Prerequisites
- Python 3.8+
- Java (JRE/JDK) installed and available on PATH. Verify with `java -version`.
- Install Python dependencies:

```powershell
pip install -r EDA/PDF_scraper/requirements.txt
```

Usage

Basic: extract tables from `input.pdf` and write a CSV with the same base name:

```powershell
python EDA/PDF_scraper/pdf_to_csv.py path\to\input.pdf
```

Provide an explicit output path (single CSV or base name for multiple tables):

```powershell
python EDA/PDF_scraper/pdf_to_csv.py path\to\input.pdf -o path\to\out.csv
```

If multiple tables are found and you don't enable `--single`, the script will write `out_table1.csv`, `out_table2.csv`, etc.

Options
- `--pages` : pages to parse (e.g. `1`, `1-3`, `all`). Default: `all`.
- `--lattice` : use lattice mode (better for tables with cell borders).
- `--no-guess` : disable area guessing.
- `--single` : merge all found tables into a single CSV (may produce uneven columns).
- `--verbose` : print full output paths.

Troubleshooting
- If extraction fails with an import or Java error:
  - Ensure `tabula-py` is installed (`pip install tabula-py`).
  - Ensure Java is installed and on PATH. On Windows, installing a JDK from AdoptOpenJDK/OpenJDK and restarting the shell usually fixes it.
- If tables are not detected correctly, try switching `--lattice` on or off, or limit `--pages`.

Example

```powershell
python EDA/PDF_scraper/pdf_to_csv.py data/sample.pdf -o data/sample.csv --pages 1-2 --lattice -v
```

Next steps / Enhancements
- Add an automated test using a small sample PDF to verify output.
- Provide an optional fallback path that uses `pdfplumber` if tabula fails.
