# Covered Interest Parity (CIP) Deviations

CIP deviations measure arbitrage opportunities in currency markets.

## Overview

The CIP spread in log terms (basis points):

```
CIP = 10000 × [i_d - (360/90)(ln F - ln S) - i_f]
```

Where:
- i_d: Domestic (foreign currency) interest rate
- i_f: Foreign (USD) interest rate
- F: 3-month forward rate
- S: Spot rate

## Interpretation

- CIP = 0: No arbitrage opportunity (parity holds)
- CIP > 0: Borrowing USD is relatively cheaper
- CIP < 0: Borrowing foreign currency is relatively cheaper

## Currencies

AUD, CAD, CHF, EUR, GBP, JPY, NZD, SEK

## Data Sources

- **Bloomberg**: FX spot rates, 3M forward points, OIS interest rates

## Outputs

- `ftsfr_cip_spreads.parquet`: Daily CIP deviations for all currencies

## Requirements

- Bloomberg Terminal running
- Python 3.10+
- xbbg package

## Setup

1. Ensure Bloomberg Terminal is running
2. Install dependencies: `pip install -r requirements.txt`
3. Run pipeline: `doit`

## Credits

Code adapted with permission from https://github.com/Kunj121/CIP
