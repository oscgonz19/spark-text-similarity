"""
Experiment runner for LSH tradeoff analysis.

Analyzes precision/recall vs bands/rows configuration and runtime.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List

from pyspark.rdd import RDD

from .lsh import lsh_threshold
from .pipeline import LSHConfig, evaluate_lsh, run_lsh_pipeline


@dataclass
class ExperimentResult:
    """Result of a single LSH experiment."""

    num_bands: int
    rows_per_band: int
    num_hashes: int
    theoretical_threshold: float
    precision: float
    recall: float
    f1: float
    num_candidates: int
    num_true_pairs: int
    num_lsh_pairs: int
    true_positives: int
    false_positives: int
    false_negatives: int
    runtime_seconds: float


def run_single_experiment(
    docs_rdd: RDD,
    ground_truth_rdd: RDD,
    num_bands: int,
    num_hashes: int = 100,
    shingle_size: int = 3,
    similarity_threshold: float = 0.5,
) -> ExperimentResult:
    """
    Run a single LSH experiment with given parameters.

    Args:
        docs_rdd: RDD of (doc_id, text)
        ground_truth_rdd: RDD of ((doc_id_1, doc_id_2), similarity)
        num_bands: Number of LSH bands
        num_hashes: Signature length (must be divisible by num_bands)
        shingle_size: Size of shingles
        similarity_threshold: Minimum similarity for "similar" pairs

    Returns:
        ExperimentResult with metrics
    """
    rows_per_band = num_hashes // num_bands

    config = LSHConfig(
        shingle_size=shingle_size,
        num_hashes=num_hashes,
        num_bands=num_bands,
        similarity_threshold=similarity_threshold,
    )

    start_time = time.time()
    result = run_lsh_pipeline(docs_rdd, config)
    runtime = time.time() - start_time

    metrics = evaluate_lsh(result, ground_truth_rdd)

    return ExperimentResult(
        num_bands=num_bands,
        rows_per_band=rows_per_band,
        num_hashes=num_hashes,
        theoretical_threshold=lsh_threshold(num_bands, rows_per_band),
        precision=metrics["precision"],
        recall=metrics["recall"],
        f1=metrics["f1"],
        num_candidates=result.num_candidates,
        num_true_pairs=metrics["num_true_pairs"],
        num_lsh_pairs=metrics["num_lsh_pairs"],
        true_positives=metrics["true_positives"],
        false_positives=metrics["false_positives"],
        false_negatives=metrics["false_negatives"],
        runtime_seconds=runtime,
    )


def run_band_sweep(
    docs_rdd: RDD,
    ground_truth_rdd: RDD,
    band_values: List[int] = None,
    num_hashes: int = 100,
    similarity_threshold: float = 0.5,
) -> List[ExperimentResult]:
    """
    Run experiments sweeping across different band configurations.

    Args:
        docs_rdd: RDD of (doc_id, text)
        ground_truth_rdd: Ground truth similar pairs
        band_values: List of num_bands values to try
        num_hashes: Total signature length
        similarity_threshold: Similarity threshold

    Returns:
        List of ExperimentResult for each configuration
    """
    if band_values is None:
        # Default: all divisors of num_hashes
        band_values = [b for b in range(1, num_hashes + 1) if num_hashes % b == 0]

    results = []
    for num_bands in band_values:
        result = run_single_experiment(
            docs_rdd=docs_rdd,
            ground_truth_rdd=ground_truth_rdd,
            num_bands=num_bands,
            num_hashes=num_hashes,
            similarity_threshold=similarity_threshold,
        )
        results.append(result)

    return results


def format_results_table(results: List[ExperimentResult]) -> str:
    """
    Format experiment results as a markdown table.

    Args:
        results: List of experiment results

    Returns:
        Markdown formatted table string
    """
    header = "| Bands | Rows | Threshold | Precision | Recall | F1 | Candidates | Runtime (s) |"
    separator = "|-------|------|-----------|-----------|--------|-----|------------|-------------|"

    rows = [header, separator]

    for r in sorted(results, key=lambda x: x.num_bands):
        row = (
            f"| {r.num_bands:5d} | {r.rows_per_band:4d} | "
            f"{r.theoretical_threshold:.3f} | "
            f"{r.precision:.3f} | {r.recall:.3f} | {r.f1:.3f} | "
            f"{r.num_candidates:10d} | {r.runtime_seconds:.2f} |"
        )
        rows.append(row)

    return "\n".join(rows)


def results_to_csv(results: List[ExperimentResult]) -> str:
    """
    Convert results to CSV format.

    Args:
        results: List of experiment results

    Returns:
        CSV string
    """
    headers = [
        "num_bands",
        "rows_per_band",
        "num_hashes",
        "theoretical_threshold",
        "precision",
        "recall",
        "f1",
        "num_candidates",
        "num_true_pairs",
        "num_lsh_pairs",
        "true_positives",
        "false_positives",
        "false_negatives",
        "runtime_seconds",
    ]

    lines = [",".join(headers)]

    for r in results:
        values = [
            str(r.num_bands),
            str(r.rows_per_band),
            str(r.num_hashes),
            f"{r.theoretical_threshold:.4f}",
            f"{r.precision:.4f}",
            f"{r.recall:.4f}",
            f"{r.f1:.4f}",
            str(r.num_candidates),
            str(r.num_true_pairs),
            str(r.num_lsh_pairs),
            str(r.true_positives),
            str(r.false_positives),
            str(r.false_negatives),
            f"{r.runtime_seconds:.4f}",
        ]
        lines.append(",".join(values))

    return "\n".join(lines)


def analyze_tradeoffs(results: List[ExperimentResult]) -> Dict[str, Any]:
    """
    Analyze tradeoffs from experiment results.

    Args:
        results: List of experiment results

    Returns:
        Dictionary with analysis summary
    """
    if not results:
        return {}

    best_f1 = max(results, key=lambda x: x.f1)
    best_precision = max(results, key=lambda x: x.precision)
    best_recall = max(results, key=lambda x: x.recall)
    fastest = min(results, key=lambda x: x.runtime_seconds)

    return {
        "best_f1": {
            "config": f"b={best_f1.num_bands}, r={best_f1.rows_per_band}",
            "f1": best_f1.f1,
            "precision": best_f1.precision,
            "recall": best_f1.recall,
        },
        "best_precision": {
            "config": f"b={best_precision.num_bands}, r={best_precision.rows_per_band}",
            "precision": best_precision.precision,
        },
        "best_recall": {
            "config": f"b={best_recall.num_bands}, r={best_recall.rows_per_band}",
            "recall": best_recall.recall,
        },
        "fastest": {
            "config": f"b={fastest.num_bands}, r={fastest.rows_per_band}",
            "runtime": fastest.runtime_seconds,
        },
        "total_experiments": len(results),
    }
