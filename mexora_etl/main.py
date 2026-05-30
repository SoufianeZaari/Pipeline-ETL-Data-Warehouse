"""Academic entry point matching the statement's expected project structure."""

from __future__ import annotations

import sys

from mexora_etl.config.settings import PROJECT_ROOT, load_settings
from mexora_etl.utils.logger import configure_logger


def run_pipeline(regenerate: bool = True) -> dict:
    """Run the validated MySQL pipeline from an academic package entry point."""
    logger = configure_logger()
    logger.info("DÉMARRAGE PIPELINE ETL MEXORA - façade académique")
    load_settings()

    scripts_dir = PROJECT_ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    import run_etl  # type: ignore

    summary = run_etl.run_pipeline(regenerate=regenerate)
    logger.info("PIPELINE TERMINÉ")
    return summary


if __name__ == "__main__":
    run_pipeline(regenerate=True)

