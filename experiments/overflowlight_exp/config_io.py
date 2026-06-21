#!/usr/bin/env python3

from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib


def load_toml(path):
    with Path(path).open("rb") as handle:
        return tomllib.load(handle)
