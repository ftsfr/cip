"""
Fetches and loads raw foreign exchange data from Bloomberg for CIP calculations.

This code is adapted with permission from https://github.com/Kunj121/CIP
"""

import sys
from pathlib import Path

sys.path.insert(0, "./src")

import pandas as pd

import chartbook

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"
END_DATE = pd.Timestamp.today().strftime("%Y-%m-%d")


def pull_fx_data(start_date="1950-01-01", end_date=END_DATE):
    """
    Fetch historical foreign exchange data from Bloomberg using xbbg.

    Returns
    -------
    dict
        Dictionary with three DataFrames:
        - 'spot_rates': Spot exchange rates
        - 'forward_points': 3M forward points
        - 'interest_rates': Interest rates (OIS)
    """
    from xbbg import blp

    # Tickers for interest rates (OIS)
    interest_rate_tickers = [
        "ADSOC CMPN Curncy",  # AUD
        "CDSOC CMPN Curncy",  # CAD
        "SFSNTC CMPN Curncy",  # CHF
        "EUSWEC CMPN Curncy",  # EUR
        "BPSWSC CMPN Curncy",  # GBP
        "JYSOC CMPN Curncy",  # JPY
        "NDSOC CMPN Curncy",  # NZD
        "SKSWTNC BGN Curncy",  # SEK
        "USSOC CMPN Curncy",  # USD
    ]

    # Tickers for 3M forward points
    forward_point_tickers = [
        "AUD3M CMPN Curncy",
        "CAD3M CMPN Curncy",
        "CHF3M CMPN Curncy",
        "EUR3M CMPN Curncy",
        "GBP3M CMPN Curncy",
        "JPY3M CMPN Curncy",
        "NZD3M CMPN Curncy",
        "SEK3M CMPN Curncy",
    ]

    # Tickers for spot rates
    spot_rate_tickers = [
        "AUD CMPN Curncy",
        "CAD CMPN Curncy",
        "CHF CMPN Curncy",
        "EUR CMPN Curncy",
        "GBP CMPN Curncy",
        "JPY CMPN Curncy",
        "NZD CMPN Curncy",
        "SEK CMPN Curncy",
    ]

    fields = ["PX_LAST"]

    def process_bloomberg_df(df):
        if not df.empty and isinstance(df.columns, pd.MultiIndex):
            df.columns = [f"{t[0]}_{t[1]}" for t in df.columns]
            df.reset_index(inplace=True)
        return df

    print(">> Pulling FX data from Bloomberg...")

    print("   Pulling interest rates...")
    interest_rates_df = process_bloomberg_df(
        blp.bdh(
            tickers=interest_rate_tickers,
            flds=fields,
            start_date=start_date,
            end_date=end_date,
        )
    )

    print("   Pulling forward points...")
    forward_points_df = process_bloomberg_df(
        blp.bdh(
            tickers=forward_point_tickers,
            flds=fields,
            start_date=start_date,
            end_date=end_date,
        )
    )

    print("   Pulling spot rates...")
    spot_rates_df = process_bloomberg_df(
        blp.bdh(
            tickers=spot_rate_tickers,
            flds=fields,
            start_date=start_date,
            end_date=end_date,
        )
    )

    return {
        "spot_rates": spot_rates_df,
        "forward_points": forward_points_df,
        "interest_rates": interest_rates_df,
    }


def load_fx_spot_rates(data_dir=DATA_DIR):
    """Load spot exchange rates from parquet file."""
    return pd.read_parquet(data_dir / "fx_spot_rates.parquet")


def load_fx_forward_points(data_dir=DATA_DIR):
    """Load 3M forward points from parquet file."""
    return pd.read_parquet(data_dir / "fx_forward_points.parquet")


def load_fx_interest_rates(data_dir=DATA_DIR):
    """Load interest rates (OIS) from parquet file."""
    return pd.read_parquet(data_dir / "fx_interest_rates.parquet")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fx_data = pull_fx_data()

    fx_data["spot_rates"].to_parquet(DATA_DIR / "fx_spot_rates.parquet")
    print(f">> Saved fx_spot_rates.parquet")

    fx_data["forward_points"].to_parquet(DATA_DIR / "fx_forward_points.parquet")
    print(f">> Saved fx_forward_points.parquet")

    fx_data["interest_rates"].to_parquet(DATA_DIR / "fx_interest_rates.parquet")
    print(f">> Saved fx_interest_rates.parquet")


if __name__ == "__main__":
    main()
