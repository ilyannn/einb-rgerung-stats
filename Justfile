#!/usr/bin/env -S just --justfile

_default:
    @just --list

run:
    python update_results.py

test:
    python -m unittest discover

lint:
    just --fmt --unstable --check
    uvx ruff check update_results.py tests
    bunx prettier --check .github/workflows/*.yml
    bunx prettier --check *.md

format:
    just --fmt --unstable
    uvx ruff format update_results.py tests
    bunx prettier --write .github/workflows/*.yml
    bunx prettier --write *.md
