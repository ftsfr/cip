"""
Create FTSFR standardized datasets for CIP spreads.

Outputs:
- ftsfr_cip_spreads.parquet: Daily CIP deviations for 8 currencies
"""

import sys
from pathlib import Path

sys.path.insert(0, "./src")

import pandas as pd

import chartbook
import calc_cip

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(">> Creating ftsfr_cip_spreads...")
    df_all = calc_cip.calculate_cip(data_dir=DATA_DIR)
    df_stacked = df_all.stack().reset_index()
    df_stacked.columns = ["ds", "unique_id", "y"]
    df_stacked = df_stacked[["unique_id", "ds", "y"]]
    df_stacked["ds"] = pd.to_datetime(df_stacked["ds"])

    df_stacked = df_stacked.dropna()
    df_stacked = df_stacked.sort_values(by=["unique_id", "ds"]).reset_index(drop=True)

    output_path = DATA_DIR / "ftsfr_cip_spreads.parquet"
    df_stacked.to_parquet(output_path, index=False)
    print(f"   Saved: {output_path.name}")
    print(f"   Records: {len(df_stacked):,}")
    print(f"   Currencies: {df_stacked['unique_id'].nunique()}")


if __name__ == "__main__":
    main()
