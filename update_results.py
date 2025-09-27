#!/usr/bin/env python3
"""Fetch the Potsdam naturalization status and append it to results.csv."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import calendar
import pathlib
import re
import sys
from html.parser import HTMLParser
from typing import Iterable, Optional
from urllib.request import urlopen

URL = "https://vv.potsdam.de/vv/produkte/173010100000003814.php"

GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "maerz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}

POSITION_DAY = {
    "anfang": 5,
    "mitte": 15,
    "ende": "last",
}


class _PlainTextExtractor(HTMLParser):
    """Collects the textual content of an HTML document."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:  # noqa: D401 - required HTMLParser override
        if data.strip():
            self._parts.append(data.strip())

    def get_text(self) -> str:
        return " ".join(self._parts)


def fetch_html(url: str = URL) -> str:
    """Return the HTML content at the given URL as UTF-8 text."""
    with urlopen(url) as response:  # nosec: URL is fixed and controlled
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_status_sentence(html: str) -> str:
    """Extract the status sentence mentioning the current processing date."""
    parser = _PlainTextExtractor()
    parser.feed(html)
    text = " ".join(parser.get_text().split())

    pattern = re.compile(
        r"Derzeit werden Anträge mit Eingangsdatum[^()]*\(Stand:\s*\d{2}\.\d{2}\.\d{4}\)\.?",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError("Status sentence not found in HTML content.")
    return match.group(0).strip()


def parse_stand_date(sentence: str) -> dt.date:
    """Extract the stand date from the status sentence."""
    match = re.search(r"Stand:\s*(\d{2})\.(\d{2})\.(\d{4})", sentence)
    if not match:
        raise ValueError("Stand date not found in sentence.")
    day, month, year = map(int, match.groups())
    return dt.date(year, month, day)


def parse_target_date(sentence: str) -> dt.date:
    """Infer the target date range mentioned in the status sentence."""
    direct_match = re.search(r"bis\s*(\d{2})\.(\d{2})\.(\d{4})", sentence)
    if direct_match:
        day, month, year = map(int, direct_match.groups())
        return dt.date(year, month, day)

    range_match = re.search(
        r"bis\s*(Anfang|Mitte|Ende)?\s*([A-Za-zÄÖÜäöüß]+)\s*(\d{4})",
        sentence,
        re.IGNORECASE,
    )
    if not range_match:
        raise ValueError("Target date not found in sentence.")

    position_raw, month_raw, year_raw = range_match.groups()
    month_key = month_raw.lower()
    month = GERMAN_MONTHS.get(month_key)
    if month is None:
        raise ValueError(f"Unknown month name: {month_raw}")

    if position_raw:
        position = position_raw.lower()
        day_reference = POSITION_DAY.get(position)
        if day_reference is None:
            raise ValueError(f"Unsupported position descriptor: {position_raw}")
        if day_reference == "last":
            day = calendar.monthrange(int(year_raw), month)[1]
        else:
            day = int(day_reference)
    else:
        # No descriptor, assume first day of month
        day = 1

    return dt.date(int(year_raw), month, day)


def read_last_row(path: pathlib.Path) -> Optional[list[str]]:
    """Return the last data row from the CSV file if it exists."""
    if not path.exists():
        return None
    last_row: Optional[list[str]] = None
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row:
                continue
            if row[0] == "retrieved_at":
                continue
            last_row = row
    return last_row


def append_row_if_changed(path: pathlib.Path, row: list[str]) -> bool:
    """Append the row if it differs from the current last row.

    Returns True when a new row is written, False otherwise.
    """
    last_row = read_last_row(path)
    if last_row == row:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if not file_exists or path.stat().st_size == 0:
            writer.writerow(
                ["retrieved_at", "stand_date", "status_text", "target_date"]
            )
        writer.writerow(row)
    return True


def collect_status(url: str = URL) -> tuple[str, dt.date, dt.date]:
    """Fetch the page and extract the status sentence, stand date, and target date."""
    html = fetch_html(url)
    sentence = extract_status_sentence(html)
    stand_date = parse_stand_date(sentence)
    target_date = parse_target_date(sentence)
    return sentence, stand_date, target_date


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Update results.csv with the latest status."
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        type=pathlib.Path,
        default=pathlib.Path("results.csv"),
        help="Path to the CSV file to update (default: results.csv)",
    )
    parser.add_argument(
        "--url",
        dest="url",
        default=URL,
        help="Override the source URL for testing purposes.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        sentence, stand_date, target_date = collect_status(args.url)
    except Exception as err:  # pragma: no cover - surfaced to CLI
        print(f"error: {err}", file=sys.stderr)
        return 1

    today = dt.date.today().isoformat()
    row = [today, stand_date.isoformat(), sentence, target_date.isoformat()]
    if append_row_if_changed(args.csv_path, row):
        print(f"Appended new row for Stand {stand_date.isoformat()} to {args.csv_path}")
    else:
        print("No change detected; CSV not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
