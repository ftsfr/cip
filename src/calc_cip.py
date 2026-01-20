"""
Calculate Covered Interest Parity (CIP) spreads from foreign exchange data.

CIP formula (log terms, in basis points):
    CIP = 10000 × [domestic_i - (logF - logS)×(360/90) - foreign_i]

Where:
- domestic_i: Foreign currency interest rate
- foreign_i: USD interest rate
- F: 3-month forward rate
- S: Spot rate

Code adapted with permission from https://github.com/Kunj121/CIP
"""

import sys
from pathlib import Path

sys.path.insert(0, "./src")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import chartbook
import pull_bbg_foreign_exchange

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"
OUTPUT_DIR = BASE_DIR / "_output"


def prepare_fx_data(spot_rates, forward_points, interest_rates):
    """
    Prepare foreign exchange data for CIP calculations.
    """
    # Set Date as index
    spot_rates = (
        spot_rates.set_index("index") if "index" in spot_rates.columns else spot_rates
    )
    forward_points = (
        forward_points.set_index("index")
        if "index" in forward_points.columns
        else forward_points
    )
    interest_rates = (
        interest_rates.set_index("index")
        if "index" in interest_rates.columns
        else interest_rates
    )

    # Standard column names
    cols = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SEK", "USD"]
    int_cols = ["ADS", "CDS", "SFS", "EUS", "BPS", "JYS", "NDS", "SKS", "USS"]

    def clean_columns(df, interest_rate=False):
        new_cols = []
        for col in df.columns:
            if "_PX_LAST" in col:
                currency = col.split()[0][:3]
                new_cols.append(currency)
            else:
                new_cols.append(col)
        df.columns = new_cols
        return df

    spot_rates = clean_columns(spot_rates)
    forward_points = clean_columns(forward_points)
    interest_rates = clean_columns(interest_rates, interest_rate=True)

    # Map interest rate columns
    ir_mapping = dict(zip(int_cols, cols))
    interest_rates = interest_rates.rename(columns=ir_mapping)

    # Convert forward points to forward rates
    # Non-JPY: forward points are per 10,000; JPY: per 100
    forward_rates = forward_points.copy()
    non_jpy_cols = [c for c in forward_rates.columns if c != "JPY"]
    if non_jpy_cols:
        forward_rates[non_jpy_cols] = forward_rates[non_jpy_cols] / 10000
    if "JPY" in forward_rates.columns:
        forward_rates["JPY"] = forward_rates["JPY"] / 100

    forward_rates = spot_rates + forward_rates

    # Rename columns
    spot_rates.columns = [f"{name}_CURNCY" for name in spot_rates.columns]
    forward_rates.columns = [f"{name}_CURNCY3M" for name in forward_rates.columns]
    interest_rates.columns = [f"{name}_IR" for name in interest_rates.columns]

    # Merge all dataframes
    df_merged = spot_rates.merge(
        forward_rates, left_index=True, right_index=True, how="inner"
    ).merge(interest_rates, left_index=True, right_index=True, how="inner")

    # Convert to reciprocal for these currencies
    reciprocal_currencies = ["EUR", "GBP", "AUD", "NZD"]
    for ccy in reciprocal_currencies:
        if f"{ccy}_CURNCY" in df_merged.columns:
            df_merged[f"{ccy}_CURNCY"] = 1.0 / df_merged[f"{ccy}_CURNCY"]
        if f"{ccy}_CURNCY3M" in df_merged.columns:
            df_merged[f"{ccy}_CURNCY3M"] = 1.0 / df_merged[f"{ccy}_CURNCY3M"]

    return df_merged


def compute_cip_spreads(df_merged):
    """
    Compute CIP spreads in basis points for all currencies.
    """
    currencies = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SEK"]

    for ccy in currencies:
        fwd_col = f"{ccy}_CURNCY3M"
        spot_col = f"{ccy}_CURNCY"
        ir_col = f"{ccy}_IR"
        usd_ir_col = "USD_IR"

        if all(
            col in df_merged.columns for col in [fwd_col, spot_col, ir_col, usd_ir_col]
        ):
            cip_col = f"CIP_{ccy}_ln"
            df_merged[cip_col] = 10000 * (
                (df_merged[ir_col] / 100.0)
                - (360.0 / 90.0)
                * (np.log(df_merged[fwd_col]) - np.log(df_merged[spot_col]))
                - (df_merged[usd_ir_col] / 100.0)
            )

    return df_merged


def clean_outliers(df_merged, window_size=45, threshold=10):
    """
    Clean outliers using rolling median absolute deviation.
    """
    currencies = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SEK"]

    for ccy in currencies:
        cip_col = f"CIP_{ccy}_ln"
        if cip_col not in df_merged.columns:
            continue

        rolling_median = df_merged[cip_col].rolling(window_size).median()
        abs_dev = (df_merged[cip_col] - rolling_median).abs()
        rolling_mad = abs_dev.rolling(window_size).mean()

        outlier_mask = (abs_dev / rolling_mad) >= threshold
        df_merged.loc[outlier_mask, cip_col] = np.nan

    return df_merged


def calculate_cip(end_date="2025-03-01", data_dir=DATA_DIR):
    """
    Calculate CIP spreads from foreign exchange data.
    """
    data_dir = Path(data_dir)

    print(">> Calculating CIP spreads...")
    spot_rates = pull_bbg_foreign_exchange.load_fx_spot_rates(data_dir=data_dir)
    forward_points = pull_bbg_foreign_exchange.load_fx_forward_points(data_dir=data_dir)
    interest_rates = pull_bbg_foreign_exchange.load_fx_interest_rates(data_dir=data_dir)

    df_merged = prepare_fx_data(spot_rates, forward_points, interest_rates)

    if end_date:
        date = pd.Timestamp(end_date).date()
        df_merged = df_merged.loc[:date]

    df_merged = compute_cip_spreads(df_merged)
    df_merged = clean_outliers(df_merged)

    # Extract just the CIP columns
    currencies = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SEK"]
    cip_cols = [f"CIP_{c}_ln" for c in currencies if f"CIP_{c}_ln" in df_merged.columns]
    spreads = df_merged[cip_cols].copy()

    # Shorten column names
    spreads.columns = [c[4:7] for c in spreads.columns]

    print(f">> Records: {len(spreads):,}")
    return spreads


def load_cip_spreads(data_dir=DATA_DIR):
    """Load calculated CIP spreads from parquet file."""
    return pd.read_parquet(data_dir / "cip_spreads.parquet")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    cip_spreads = calculate_cip()
    cip_spreads.to_parquet(DATA_DIR / "cip_spreads.parquet")
    print(">> Saved cip_spreads.parquet")


if __name__ == "__main__":
    main()
