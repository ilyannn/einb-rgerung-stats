# Einbürgerung Processing Status

This repository tracks the public processing notice from [Potsdam's naturalization group](https://vv.potsdam.de/vv/produkte/arbeitsgruppe-einbuergerung/173010100000003814.php) and keeps a timestamped history in `results.csv`.

## How It Works

`update_results.py` downloads the page, extracts the sentence that contains the currently processed application date, parses both the "Stand" date and the referenced application intake date, and appends them to `results.csv` together with today's date. The script only uses Python's standard library.

Before writing a new row the script checks the latest entry in `results.csv` and skips the update when nothing changed. When a new value appears, the CSV will look like this:

```csv
retrieved_at,stand_date,status_text,target_date
2025-02-22,2025-08-28,"Derzeit werden Anträge mit Eingangsdatum bis Ende April 2023 bearbeitet (Stand: 28.08.2025).",2023-04-30
```

**Columns explained:**

- `retrieved_at`: Date when the status was checked
- `stand_date`: Official status date from the website
- `status_text`: Full German status message
- `target_date`: Last day of the month being processed

## Prerequisites

- Python 3.11+ (no additional packages required)
- `just` command runner (optional, for convenience)
- `uv` with `uvx` (for linting/formatting)
- Bun with `bunx` (only required if you plan to run the prettier lint/format recipes)

## Usage

```sh
just run
```

or

```sh
python update_results.py
```

**Optional arguments:**

- `--csv PATH` – store the output in a different CSV file
- `--url URL` – fetch from a different source (useful for testing with saved HTML)

## Tests

Run the unit tests with:

```sh
just test
```

or directly with Python:

```sh
python -m unittest discover
```

Tests rely exclusively on the standard library and mock the network call so no internet connection is required.

## Automation

### Local Development

A small `just` recipe file is included for convenience:

- `just run` executes the script.
- `just format` formats the code.
- `just lint` checks the format and lints.
- `just test` runs the unit tests.

Install `just` from https://github.com/casey/just and `uv` (for `uvx`) from https://docs.astral.sh/uv/ if they are not already available on your system.

### GitHub Actions

Two workflows are configured for automated operation:

#### CI Workflow

Runs on every push and pull request to the main branch:

- **Linting**: Python code style checks with `ruff`
- **Formatting**: Code formatting validation
- **Testing**: Unit test execution

#### Scheduled Updates

Automatically updates the status data every 8 hours:

- **Schedule**: 07:00, 13:00, 21:00 CET (04:00, 12:00, 20:00 UTC)
- **Process**: Fetches latest status, commits changes if data updated
- **Notifications**: Creates GitHub issues on failure
- **Manual trigger**: Can be run manually from the Actions tab

The automated updates ensure the dataset stays current without manual intervention.

**Setup**: Push the workflows to your GitHub repository to activate automated runs. Ensure the workflow token can write repository contents (GitHub Actions → General → Workflow permissions → "Read and write" or set `permissions: contents: write` in the workflow) so the scheduled job can commit `results.csv` updates. No other configuration required.
