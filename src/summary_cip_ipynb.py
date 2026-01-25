# %%
"""
# Covered Interest Parity (CIP) Deviations Summary

CIP deviations measure arbitrage opportunities in currency markets.
"""

# %%
import sys
sys.path.insert(0, "./src")

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import chartbook

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"

# %%
"""
## Methodology

The CIP spread in log terms (basis points) is calculated as:

$$
\\text{CIP} = 10000 \\times \\left[ i_d - \\frac{360}{90}(\\ln F - \\ln S) - i_f \\right]
$$

Where:
- $i_d$: Domestic (foreign currency) interest rate
- $i_f$: Foreign (USD) interest rate
- $F$: 3-month forward rate
- $S$: Spot rate

### Interpretation

- CIP = 0: No arbitrage opportunity (parity holds)
- CIP > 0: Borrowing USD is relatively cheaper
- CIP < 0: Borrowing foreign currency is relatively cheaper

### Data Sources

- Bloomberg FX spot rates
- Bloomberg 3M forward points
- Bloomberg OIS interest rates
"""

# %%
"""
## Data Overview
"""

# %%
df = pd.read_parquet(DATA_DIR / "ftsfr_cip_spreads.parquet")
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nDate range: {df['ds'].min()} to {df['ds'].max()}")
print(f"Number of currencies: {df['unique_id'].nunique()}")

# %%
print("\nCurrencies:")
for ccy in sorted(df['unique_id'].unique()):
    print(f"  {ccy}")

# %%
"""
### Summary Statistics
"""

# %%
cip_wide = df.pivot(index='ds', columns='unique_id', values='y')
cip_stats = cip_wide.describe().T
cip_stats['skewness'] = cip_wide.skew()
cip_stats['kurtosis'] = cip_wide.kurtosis()
print(cip_stats[['mean', 'std', 'min', 'max', 'skewness', 'kurtosis']].round(2).to_string())

# %%
"""
### CIP Spreads Time Series
"""

# %%
fig, ax = plt.subplots(figsize=(14, 8))

for ccy in cip_wide.columns:
    ax.plot(cip_wide.index, cip_wide[ccy], label=ccy, alpha=0.8, linewidth=1)

ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax.set_xlabel('Date')
ax.set_ylabel('CIP Spread (bps)')
ax.set_title('Covered Interest Parity Deviations')
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_ylim([-50, 210])

plt.tight_layout()
plt.savefig(DATA_DIR.parent / "_output" / "cip_spreads.png", dpi=150, bbox_inches='tight')
plt.show()

# %%
"""
### Major Currencies Only
"""

# %%
fig, ax = plt.subplots(figsize=(12, 6))

major = ['EUR', 'GBP', 'JPY', 'CHF']
for ccy in major:
    if ccy in cip_wide.columns:
        ax.plot(cip_wide.index, cip_wide[ccy], label=ccy, alpha=0.8)

ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax.set_xlabel('Date')
ax.set_ylabel('CIP Spread (bps)')
ax.set_title('CIP Deviations - Major Currencies')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(DATA_DIR.parent / "_output" / "cip_major.png", dpi=150, bbox_inches='tight')
plt.show()

# %%
"""
### Correlation Matrix
"""

# %%
fig, ax = plt.subplots(figsize=(10, 8))
corr = cip_wide.corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=ax)
ax.set_title('CIP Spread Correlations')
plt.tight_layout()
plt.savefig(DATA_DIR.parent / "_output" / "cip_correlation.png", dpi=150, bbox_inches='tight')
plt.show()

# %%
"""
## Data Definitions

### CIP Spreads (ftsfr_cip_spreads)

| Variable | Description |
|----------|-------------|
| unique_id | Currency code (e.g., EUR, GBP, JPY) |
| ds | Date |
| y | CIP spread in basis points |

### Currencies

| Code | Currency |
|------|----------|
| AUD | Australian Dollar |
| CAD | Canadian Dollar |
| CHF | Swiss Franc |
| EUR | Euro |
| GBP | British Pound |
| JPY | Japanese Yen |
| NZD | New Zealand Dollar |
| SEK | Swedish Krona |
"""
