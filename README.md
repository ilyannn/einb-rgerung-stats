# Einbürgerung Processing Status

This repository tracks the public processing notice from https://vv.potsdam.de/vv/produkte/173010100000003814.php and keeps a timestamped history in `results.csv`.

## Script

`update_results.py` downloads the page, extracts the sentence that contains the currently processed application date, parses both the "Stand" date and the referenced application intake date, and appends them to `results.csv` together with today's date. The script only uses Python's standard library.

Before writing a new row the script checks the latest entry in `results.csv` and skips the update when nothing changed. When a new value appears, the CSV will look like this:

```
retrieved_at,stand_date,status_text,target_date
2025-02-22,2025-08-28,"Derzeit werden Anträge mit Eingangsdatum bis Ende April 2023 bearbeitet (Stand: 28.08.2025).",2023-04-30
```

## Usage

```
python update_results.py
```

Optional arguments:

- `--csv PATH` – store the output in a different CSV file.
- `--url URL` – fetch from a different source (useful for testing with saved HTML).

## Tests

Run the unit tests with:

```
just test
```

or directly with Python:

```
python -m unittest discover
```

Tests rely exclusively on the standard library and mock the network call so no internet connection is required.

## Automation

A small `just` recipe file is included for convenience:

- `just run` executes the script.
- `just test` runs the unit tests.
- `just lint` runs `uvx ruff check` on the sources.
- `just format` formats the code with `uvx ruff format`.

Install `just` from https://github.com/casey/just and `uv` (for `uvx`) from https://docs.astral.sh/uv/ if they are not already available on your system.
