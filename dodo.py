"""
Doit build file for CIP (Covered Interest Parity) pipeline.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import chartbook

sys.path.insert(1, "./src/")


# Bloomberg Terminal check - runs at module load time
def _check_bloomberg_terminal():
    """Check Bloomberg Terminal availability with env var override."""
    # Skip prompt if environment variable is set
    if os.environ.get("BLOOMBERG_TERMINAL_OPEN", "").lower() in ("true", "1", "yes"):
        print("BLOOMBERG_TERMINAL_OPEN=True detected, skipping prompt...")
        return True

    # Interactive prompt
    response = input("Do you have the Bloomberg terminal open in the background? [Y/n]: ")
    if response.lower() in ('n', 'no'):
        raise SystemExit(
            "\nBloomberg Terminal not available. Exiting.\n"
            "Tip: Set BLOOMBERG_TERMINAL_OPEN=True to skip this prompt."
        )
    return True


_check_bloomberg_terminal()

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"
OUTPUT_DIR = BASE_DIR / "_output"
NOTEBOOK_BUILD_DIR = OUTPUT_DIR / "_notebook_build"
OS_TYPE = "nix" if platform.system() != "Windows" else "windows"


def jupyter_execute_notebook(notebook):
    """Execute a notebook and convert to HTML."""
    subprocess.run(
        [
            "jupyter",
            "nbconvert",
            "--execute",
            "--to",
            "html",
            "--output-dir",
            str(OUTPUT_DIR),
            str(notebook),
        ],
        check=True,
    )


def task_config():
    """Create directories for data and output."""

    def create_dirs():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        NOTEBOOK_BUILD_DIR.mkdir(parents=True, exist_ok=True)

    return {
        "actions": [create_dirs],
        "targets": [DATA_DIR, OUTPUT_DIR, NOTEBOOK_BUILD_DIR],
        "verbosity": 2,
    }


def task_pull():
    """Pull FX data from Bloomberg."""
    return {
        "actions": ["python src/pull_bbg_foreign_exchange.py"],
        "file_dep": ["src/pull_bbg_foreign_exchange.py"],
        "targets": [
            DATA_DIR / "fx_spot_rates.parquet",
            DATA_DIR / "fx_forward_points.parquet",
            DATA_DIR / "fx_interest_rates.parquet",
        ],
        "verbosity": 2,
        "task_dep": ["config"],
    }


def task_calc():
    """Calculate CIP spreads."""
    return {
        "actions": ["python src/calc_cip.py"],
        "file_dep": [
            "src/calc_cip.py",
            DATA_DIR / "fx_spot_rates.parquet",
            DATA_DIR / "fx_forward_points.parquet",
            DATA_DIR / "fx_interest_rates.parquet",
        ],
        "targets": [DATA_DIR / "cip_spreads.parquet"],
        "verbosity": 2,
        "task_dep": ["pull"],
    }


def task_format():
    """Create FTSFR standardized datasets."""
    return {
        "actions": ["python src/create_ftsfr_datasets.py"],
        "file_dep": [
            "src/create_ftsfr_datasets.py",
            DATA_DIR / "cip_spreads.parquet",
        ],
        "targets": [DATA_DIR / "ftsfr_cip_spreads.parquet"],
        "verbosity": 2,
        "task_dep": ["calc"],
    }


def task_run_notebooks():
    """Execute summary notebook and convert to HTML."""
    notebook_py = BASE_DIR / "src" / "summary_cip_ipynb.py"
    notebook_ipynb = NOTEBOOK_BUILD_DIR / "summary_cip.ipynb"

    def run_notebook():
        subprocess.run(
            ["ipynb-py-convert", str(notebook_py), str(notebook_ipynb)],
            check=True,
        )
        jupyter_execute_notebook(notebook_ipynb)

    return {
        "actions": [run_notebook],
        "file_dep": [
            notebook_py,
            DATA_DIR / "ftsfr_cip_spreads.parquet",
        ],
        "targets": [
            notebook_ipynb,
            OUTPUT_DIR / "summary_cip.html",
        ],
        "verbosity": 2,
        "task_dep": ["format"],
    }


def task_generate_pipeline_site():
    """Generate chartbook documentation site."""
    return {
        "actions": ["chartbook build -f"],
        "file_dep": [
            "chartbook.toml",
            NOTEBOOK_BUILD_DIR / "summary_cip.ipynb",
        ],
        "targets": [BASE_DIR / "docs" / "index.html"],
        "verbosity": 2,
        "task_dep": ["run_notebooks"],
    }
