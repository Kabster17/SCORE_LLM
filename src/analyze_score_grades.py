"""Analyse completed SCORE grader outputs.

This script is the cleaned post-grading analysis stage for a public repository.
It computes total scores, internal consistency, pairwise effect sizes, model
rankings, and publication-friendly summary figures.
"""

from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pingouin import cronbach_alpha

from utils import SCORE_COLUMNS, ensure_directory, read_tabular_file, validate_score_columns



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse completed SCORE grading outputs.")
    parser.add_argument("--input", required=True, help="Long-format CSV or Excel file.")
    parser.add_argument("--output-dir", required=True, help="Directory to save results.")
    return parser.parse_args()



def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """Compute Cliff's delta effect size."""
    n1, n2 = len(x), len(y)
    delta = sum(1 if xi > yj else (-1 if xi < yj else 0) for xi in x for yj in y) / (n1 * n2)
    return float(delta)



def interpret_delta(delta: float) -> str:
    """Return a qualitative interpretation for Cliff's delta."""
    abs_delta = abs(delta)
    if abs_delta < 0.147:
        return "Negligible"
    if abs_delta < 0.330:
        return "Small"
    if abs_delta < 0.474:
        return "Medium"
    return "Large"



def summarise_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Add total SCORE and summarise model performance within each domain."""
    df = df.copy()
    df["total_score"] = df[SCORE_COLUMNS].sum(axis=1)
    summary = (
        df.groupby(["domain", "model"], as_index=False)["total_score"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    summary.columns = ["domain", "model", "mean_total_score", "sd_total_score", "n"]
    return df, summary



def cronbach_by_domain(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate Cronbach's alpha for each domain."""
    rows = []
    for domain, domain_df in df.groupby("domain"):
        alpha, ci = cronbach_alpha(domain_df[SCORE_COLUMNS])
        rows.append(
            {
                "domain": domain,
                "cronbach_alpha": alpha,
                "ci_lower": ci[0],
                "ci_upper": ci[1],
            }
        )
    return pd.DataFrame(rows)



def pairwise_deltas(df: pd.DataFrame) -> pd.DataFrame:
    """Compute pairwise Cliff's delta within each domain."""
    rows = []
    for domain, domain_df in df.groupby("domain"):
        totals_by_model = {
            model: model_df["total_score"].to_numpy()
            for model, model_df in domain_df.groupby("model")
        }
        for left_model, right_model in combinations(sorted(totals_by_model.keys()), 2):
            delta = cliffs_delta(totals_by_model[left_model], totals_by_model[right_model])
            rows.append(
                {
                    "domain": domain,
                    "left_model": left_model,
                    "right_model": right_model,
                    "cliffs_delta": delta,
                    "effect_size": interpret_delta(delta),
                }
            )
    return pd.DataFrame(rows)



def create_alpha_figure(alpha_df: pd.DataFrame, output_dir: Path) -> None:
    """Create a bar chart of Cronbach's alpha values."""
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(alpha_df))
    y = alpha_df["cronbach_alpha"].to_numpy()
    yerr = np.vstack([
        y - alpha_df["ci_lower"].to_numpy(),
        alpha_df["ci_upper"].to_numpy() - y,
    ])

    bars = ax.bar(x, y, edgecolor="black", linewidth=1.5)
    ax.errorbar(x, y, yerr=yerr, fmt="none", color="black", capsize=6, linewidth=1.5)
    ax.set_xticks(x)
    ax.set_xticklabels(alpha_df["domain"].tolist())
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Cronbach's alpha")
    ax.set_title("Internal consistency by domain")
    ax.axhline(0.7, linestyle="--", linewidth=1)
    ax.axhline(0.8, linestyle="--", linewidth=1)
    ax.axhline(0.9, linestyle="--", linewidth=1)

    for bar, alpha in zip(bars, y):
        ax.text(bar.get_x() + bar.get_width() / 2, alpha + 0.03, f"{alpha:.3f}", ha="center")

    fig.tight_layout()
    fig.savefig(output_dir / "cronbach_alpha.png", dpi=300, bbox_inches="tight")
    plt.close(fig)



def create_rankings_figure(summary_df: pd.DataFrame, output_dir: Path) -> None:
    """Create grouped bar chart of mean total scores."""
    pivot_df = summary_df.pivot(index="domain", columns="model", values="mean_total_score")

    fig, ax = plt.subplots(figsize=(11, 6))
    pivot_df.plot(kind="bar", ax=ax, edgecolor="black")
    ax.set_ylabel("Mean total SCORE")
    ax.set_title("Model rankings by domain")
    ax.legend(title="Model")
    fig.tight_layout()
    fig.savefig(output_dir / "model_rankings.png", dpi=300, bbox_inches="tight")
    plt.close(fig)



def main() -> None:
    args = parse_args()
    output_dir = ensure_directory(args.output_dir)

    df = read_tabular_file(args.input)
    validate_score_columns(df)

    required_metadata = ["domain", "model", "response_id"]
    missing_metadata = [column for column in required_metadata if column not in df.columns]
    if missing_metadata:
        raise ValueError("Missing required metadata columns: " + ", ".join(missing_metadata))

    scored_df, summary_df = summarise_totals(df)
    alpha_df = cronbach_by_domain(scored_df)
    delta_df = pairwise_deltas(scored_df)

    scored_df.to_csv(output_dir / "scored_with_totals.csv", index=False)
    summary_df.to_csv(output_dir / "model_summary.csv", index=False)
    alpha_df.to_csv(output_dir / "cronbach_alpha_summary.csv", index=False)
    delta_df.to_csv(output_dir / "cliffs_delta_summary.csv", index=False)

    create_alpha_figure(alpha_df, output_dir)
    create_rankings_figure(summary_df, output_dir)

    print("Saved outputs to:")
    print(f"  - {output_dir / 'scored_with_totals.csv'}")
    print(f"  - {output_dir / 'model_summary.csv'}")
    print(f"  - {output_dir / 'cronbach_alpha_summary.csv'}")
    print(f"  - {output_dir / 'cliffs_delta_summary.csv'}")
    print(f"  - {output_dir / 'cronbach_alpha.png'}")
    print(f"  - {output_dir / 'model_rankings.png'}")


if __name__ == "__main__":
    main()
