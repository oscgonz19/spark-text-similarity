"""
Visualization module for LSH pipeline analysis.

Generates charts and diagrams for documentation and analysis.
"""

import os
from typing import List, Tuple, Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# Set style for all plots
plt.style.use("seaborn-v0_8-whitegrid")
COLORS = {
    "primary": "#2563eb",  # Blue
    "secondary": "#7c3aed",  # Purple
    "success": "#059669",  # Green
    "warning": "#d97706",  # Orange
    "danger": "#dc2626",  # Red
    "gray": "#6b7280",
}


def s_curve_probability(s: float, b: int, r: int) -> float:
    """Calculate probability of becoming candidates given similarity s."""
    return 1 - (1 - s**r) ** b


def lsh_threshold(b: int, r: int) -> float:
    """Calculate the threshold where P(candidate) = 0.5."""
    return (1 / b) ** (1 / r)


def plot_s_curve(
    configs: List[Tuple[int, int]],
    output_path: str = "docs/images/s_curve.png",
    figsize: Tuple[int, int] = (10, 6),
) -> str:
    """
    Plot S-curve for different band/row configurations.

    Args:
        configs: List of (bands, rows) tuples
        output_path: Path to save the figure
        figsize: Figure size

    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    similarities = np.linspace(0, 1, 1000)
    colors = [COLORS["primary"], COLORS["secondary"], COLORS["success"], COLORS["warning"]]

    for i, (b, r) in enumerate(configs):
        probs = [s_curve_probability(s, b, r) for s in similarities]
        threshold = lsh_threshold(b, r)
        color = colors[i % len(colors)]

        ax.plot(
            similarities,
            probs,
            label=f"b={b}, r={r} (τ≈{threshold:.2f})",
            linewidth=2.5,
            color=color,
        )

        # Mark threshold point
        ax.plot(threshold, 0.5, "o", color=color, markersize=8)
        ax.axvline(x=threshold, color=color, linestyle="--", alpha=0.3)

    ax.axhline(y=0.5, color=COLORS["gray"], linestyle="-", alpha=0.5, linewidth=1)
    ax.set_xlabel("True Jaccard Similarity", fontsize=12)
    ax.set_ylabel("P(Candidate Pair)", fontsize=12)
    ax.set_title("LSH S-Curve: Probability of Becoming Candidates", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Add annotation
    ax.annotate(
        "Threshold τ\n(P=0.5)",
        xy=(0.55, 0.5),
        xytext=(0.75, 0.3),
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color=COLORS["gray"]),
    )

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()

    return output_path


def plot_metrics_comparison(
    results: List[dict],
    output_path: str = "docs/images/metrics_comparison.png",
    figsize: Tuple[int, int] = (12, 5),
) -> str:
    """
    Plot precision, recall, and F1 for different configurations.

    Args:
        results: List of dicts with keys: bands, precision, recall, f1, candidates
        output_path: Path to save the figure

    Returns:
        Path to saved figure
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    bands = [r["bands"] for r in results]
    precision = [r["precision"] for r in results]
    recall = [r["recall"] for r in results]
    f1 = [r["f1"] for r in results]
    candidates = [r["candidates"] for r in results]

    # Left plot: Metrics
    ax1 = axes[0]
    x = np.arange(len(bands))
    width = 0.25

    bars1 = ax1.bar(x - width, precision, width, label="Precision", color=COLORS["primary"])
    bars2 = ax1.bar(x, recall, width, label="Recall", color=COLORS["secondary"])
    bars3 = ax1.bar(x + width, f1, width, label="F1 Score", color=COLORS["success"])

    ax1.set_xlabel("Number of Bands (b)", fontsize=11)
    ax1.set_ylabel("Score", fontsize=11)
    ax1.set_title("Precision, Recall, and F1 by Configuration", fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels([str(b) for b in bands])
    ax1.legend(loc="lower right")
    ax1.set_ylim(0, 1.1)

    # Highlight optimal
    optimal_idx = np.argmax(f1)
    ax1.axvspan(optimal_idx - 0.4, optimal_idx + 0.4, alpha=0.2, color=COLORS["success"])

    # Right plot: Candidates vs F1
    ax2 = axes[1]
    ax2.scatter(candidates, f1, s=100, c=COLORS["primary"], alpha=0.7, edgecolors="white")

    for i, (c, score, b) in enumerate(zip(candidates, f1, bands)):
        ax2.annotate(f"b={b}", (c, score), textcoords="offset points", xytext=(5, 5), fontsize=9)

    ax2.set_xlabel("Number of Candidates", fontsize=11)
    ax2.set_ylabel("F1 Score", fontsize=11)
    ax2.set_title("Candidates vs F1 Score Trade-off", fontsize=12, fontweight="bold")

    # Highlight optimal region
    ax2.axhline(y=0.9, color=COLORS["success"], linestyle="--", alpha=0.5, label="F1 ≥ 0.9")
    ax2.legend()

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()

    return output_path


def plot_scalability(
    output_path: str = "docs/images/scalability.png",
    figsize: Tuple[int, int] = (10, 6),
) -> str:
    """
    Plot scalability comparison: Brute Force vs LSH.

    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Data points
    corpus_sizes = [100, 1000, 10000, 100000, 1000000]
    brute_force = [n * (n - 1) / 2 for n in corpus_sizes]
    lsh_candidates = [int(bf * 0.16) for bf in brute_force]  # ~84% reduction

    x = np.arange(len(corpus_sizes))
    width = 0.35

    bars1 = ax.bar(x - width / 2, brute_force, width, label="Brute Force O(n²)", color=COLORS["danger"], alpha=0.8)
    bars2 = ax.bar(x + width / 2, lsh_candidates, width, label="LSH Candidates", color=COLORS["success"], alpha=0.8)

    ax.set_xlabel("Corpus Size (documents)", fontsize=11)
    ax.set_ylabel("Number of Comparisons", fontsize=11)
    ax.set_title("Scalability: Brute Force vs LSH", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{n:,}" for n in corpus_sizes], rotation=45)
    ax.legend()
    ax.set_yscale("log")

    # Add reduction percentage labels
    for i, (bf, lsh) in enumerate(zip(brute_force, lsh_candidates)):
        reduction = (1 - lsh / bf) * 100
        ax.annotate(
            f"-{reduction:.0f}%",
            xy=(i + width / 2, lsh),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            color=COLORS["success"],
            fontweight="bold",
        )

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()

    return output_path


def plot_pipeline_diagram(
    output_path: str = "docs/images/pipeline_diagram.png",
    figsize: Tuple[int, int] = (14, 8),
) -> str:
    """
    Create a visual pipeline diagram.

    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")

    # Box properties
    box_height = 1.5
    box_width = 2.2
    y_center = 4

    stages = [
        ("Documents\nCorpus", COLORS["gray"], 1),
        ("Shingling\n(k-grams)", COLORS["primary"], 3.5),
        ("MinHash\n(signatures)", COLORS["secondary"], 6),
        ("LSH\n(banding)", COLORS["warning"], 8.5),
        ("Verify\n(Jaccard)", COLORS["success"], 11),
    ]

    # Draw boxes and arrows
    for i, (label, color, x) in enumerate(stages):
        # Box
        rect = mpatches.FancyBboxPatch(
            (x - box_width / 2, y_center - box_height / 2),
            box_width,
            box_height,
            boxstyle="round,pad=0.05,rounding_size=0.2",
            facecolor=color,
            edgecolor="white",
            linewidth=2,
            alpha=0.9,
        )
        ax.add_patch(rect)

        # Label
        ax.text(x, y_center, label, ha="center", va="center", fontsize=11, color="white", fontweight="bold")

        # Arrow to next stage
        if i < len(stages) - 1:
            next_x = stages[i + 1][2]
            ax.annotate(
                "",
                xy=(next_x - box_width / 2 - 0.1, y_center),
                xytext=(x + box_width / 2 + 0.1, y_center),
                arrowprops=dict(arrowstyle="->", color=COLORS["gray"], lw=2),
            )

    # Add descriptions below
    descriptions = [
        ("N docs", 1),
        ("Sets of\nshingles", 3.5),
        ("Compact\nsignatures", 6),
        ("Candidate\npairs", 8.5),
        ("Similar\npairs", 11),
    ]

    for desc, x in descriptions:
        ax.text(x, y_center - 1.5, desc, ha="center", va="top", fontsize=9, color=COLORS["gray"])

    # Title
    ax.text(7, 7, "LSH Similarity Pipeline", ha="center", va="center", fontsize=16, fontweight="bold")

    # Complexity annotation
    ax.text(
        7,
        1.5,
        "Complexity: O(N) + O(candidates) instead of O(N²)",
        ha="center",
        va="center",
        fontsize=11,
        style="italic",
        color=COLORS["gray"],
    )

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()

    return output_path


def plot_threshold_heatmap(
    output_path: str = "docs/images/threshold_heatmap.png",
    figsize: Tuple[int, int] = (10, 8),
) -> str:
    """
    Create heatmap of thresholds for different b and r combinations.

    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    bands_range = [5, 10, 20, 25, 50, 100]
    rows_range = [2, 4, 5, 10, 20, 50]

    # Calculate thresholds
    thresholds = np.zeros((len(rows_range), len(bands_range)))
    for i, r in enumerate(rows_range):
        for j, b in enumerate(bands_range):
            thresholds[i, j] = lsh_threshold(b, r)

    # Create heatmap
    im = ax.imshow(thresholds, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=1)

    # Labels
    ax.set_xticks(np.arange(len(bands_range)))
    ax.set_yticks(np.arange(len(rows_range)))
    ax.set_xticklabels(bands_range)
    ax.set_yticklabels(rows_range)
    ax.set_xlabel("Number of Bands (b)", fontsize=11)
    ax.set_ylabel("Rows per Band (r)", fontsize=11)
    ax.set_title("LSH Threshold τ by Configuration\n(τ = (1/b)^(1/r))", fontsize=14, fontweight="bold")

    # Add text annotations
    for i in range(len(rows_range)):
        for j in range(len(bands_range)):
            value = thresholds[i, j]
            color = "white" if value > 0.5 else "black"
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", color=color, fontsize=10)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, label="Threshold τ")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()

    return output_path


def plot_experiment_results(
    output_path: str = "docs/images/experiment_results.png",
    figsize: Tuple[int, int] = (12, 8),
) -> str:
    """
    Create comprehensive experiment results visualization.

    Returns:
        Path to saved figure
    """
    fig, axes = plt.subplots(2, 2, figsize=figsize)

    # Experiment data
    configs = [
        {"b": 5, "r": 20, "threshold": 0.923, "precision": 0, "recall": 0, "f1": 0, "candidates": 0},
        {"b": 10, "r": 10, "threshold": 0.794, "precision": 1.0, "recall": 0.19, "f1": 0.323, "candidates": 12},
        {"b": 20, "r": 5, "threshold": 0.549, "precision": 1.0, "recall": 0.85, "f1": 0.917, "candidates": 775},
        {"b": 25, "r": 4, "threshold": 0.447, "precision": 1.0, "recall": 1.0, "f1": 1.0, "candidates": 2187},
        {"b": 50, "r": 2, "threshold": 0.141, "precision": 1.0, "recall": 1.0, "f1": 1.0, "candidates": 4947},
    ]

    bands = [c["b"] for c in configs]

    # Plot 1: Threshold vs Bands
    ax1 = axes[0, 0]
    thresholds = [c["threshold"] for c in configs]
    ax1.plot(bands, thresholds, "o-", color=COLORS["primary"], linewidth=2, markersize=8)
    ax1.axhline(y=0.5, color=COLORS["gray"], linestyle="--", label="Target τ=0.5")
    ax1.set_xlabel("Bands (b)")
    ax1.set_ylabel("Threshold τ")
    ax1.set_title("Threshold by Configuration", fontweight="bold")
    ax1.legend()

    # Plot 2: F1 Score
    ax2 = axes[0, 1]
    f1_scores = [c["f1"] for c in configs]
    colors = [COLORS["success"] if f >= 0.9 else COLORS["warning"] if f >= 0.5 else COLORS["danger"] for f in f1_scores]
    ax2.bar(range(len(bands)), f1_scores, color=colors)
    ax2.set_xticks(range(len(bands)))
    ax2.set_xticklabels([f"b={b}" for b in bands])
    ax2.set_ylabel("F1 Score")
    ax2.set_title("F1 Score by Configuration", fontweight="bold")
    ax2.axhline(y=0.9, color=COLORS["gray"], linestyle="--", alpha=0.5)

    # Plot 3: Candidates
    ax3 = axes[1, 0]
    candidates = [c["candidates"] for c in configs]
    ax3.bar(range(len(bands)), candidates, color=COLORS["secondary"])
    ax3.set_xticks(range(len(bands)))
    ax3.set_xticklabels([f"b={b}" for b in bands])
    ax3.set_ylabel("Candidate Pairs")
    ax3.set_title("Candidates Generated", fontweight="bold")
    ax3.axhline(y=4950, color=COLORS["danger"], linestyle="--", label="All pairs (4950)")
    ax3.legend()

    # Plot 4: Precision-Recall
    ax4 = axes[1, 1]
    precision = [c["precision"] for c in configs if c["precision"] > 0]
    recall = [c["recall"] for c in configs if c["recall"] > 0]
    bands_filtered = [c["b"] for c in configs if c["precision"] > 0]
    ax4.scatter(recall, precision, s=100, c=COLORS["primary"])
    for i, b in enumerate(bands_filtered):
        ax4.annotate(f"b={b}", (recall[i], precision[i]), textcoords="offset points", xytext=(5, 5))
    ax4.set_xlabel("Recall")
    ax4.set_ylabel("Precision")
    ax4.set_title("Precision-Recall Curve", fontweight="bold")
    ax4.set_xlim(0, 1.1)
    ax4.set_ylim(0, 1.1)

    plt.suptitle("LSH Experiment Results (100 docs, threshold=0.5)", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()

    return output_path


def generate_all_visualizations(output_dir: str = "docs/images") -> List[str]:
    """
    Generate all visualizations for documentation.

    Args:
        output_dir: Directory to save images

    Returns:
        List of paths to generated images
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    print("Generating visualizations...")

    # 1. S-Curve
    print("  - S-Curve probability chart...")
    paths.append(
        plot_s_curve(
            configs=[(10, 10), (20, 5), (25, 4), (50, 2)],
            output_path=f"{output_dir}/s_curve.png",
        )
    )

    # 2. Metrics comparison
    print("  - Metrics comparison chart...")
    results = [
        {"bands": 10, "precision": 1.0, "recall": 0.19, "f1": 0.323, "candidates": 12},
        {"bands": 20, "precision": 1.0, "recall": 0.85, "f1": 0.917, "candidates": 775},
        {"bands": 25, "precision": 1.0, "recall": 1.0, "f1": 1.0, "candidates": 2187},
        {"bands": 50, "precision": 1.0, "recall": 1.0, "f1": 1.0, "candidates": 4947},
    ]
    paths.append(plot_metrics_comparison(results, output_path=f"{output_dir}/metrics_comparison.png"))

    # 3. Scalability
    print("  - Scalability chart...")
    paths.append(plot_scalability(output_path=f"{output_dir}/scalability.png"))

    # 4. Pipeline diagram
    print("  - Pipeline diagram...")
    paths.append(plot_pipeline_diagram(output_path=f"{output_dir}/pipeline_diagram.png"))

    # 5. Threshold heatmap
    print("  - Threshold heatmap...")
    paths.append(plot_threshold_heatmap(output_path=f"{output_dir}/threshold_heatmap.png"))

    # 6. Experiment results
    print("  - Experiment results...")
    paths.append(plot_experiment_results(output_path=f"{output_dir}/experiment_results.png"))

    print(f"\nGenerated {len(paths)} visualizations in {output_dir}/")
    return paths


if __name__ == "__main__":
    generate_all_visualizations()
