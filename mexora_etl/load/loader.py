"""Loader facade for the validated MySQL Data Warehouse pipeline."""

from __future__ import annotations

import sys

from mexora_etl.config.settings import PROJECT_ROOT


def load_validated_mysql_dw() -> dict:
    """Load the processed star schema using the project production loader."""
    scripts_dir = PROJECT_ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import load  # type: ignore

    return load.load()

