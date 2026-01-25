"""Generate interactive HTML chart for CIP Deviations."""

import pandas as pd
import plotly.express as px
from pathlib import Path

# Get the project root (one level up from src/)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "_data"
OUTPUT_DIR = PROJECT_ROOT / "_output"


def generate_cip_chart():
    """Generate CIP deviations time series chart."""
    # Load CIP spreads data
    df = pd.read_parquet(DATA_DIR / "ftsfr_cip_spreads.parquet")

    # Sort by date
    df = df.sort_values(['unique_id', 'ds'])

    # Create line chart
    fig = px.line(
        df,
        x="ds",
        y="y",
        color="unique_id",
        title="Covered Interest Parity Deviations",
        labels={
            "ds": "Date",
            "y": "CIP Spread (bps)",
            "unique_id": "Currency"
        }
    )

    # Add zero reference line
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)

    # Update layout
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
    )

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save chart
    output_path = OUTPUT_DIR / "cip_deviations.html"
    fig.write_html(str(output_path))
    print(f"Chart saved to {output_path}")

    return fig


if __name__ == "__main__":
    generate_cip_chart()
