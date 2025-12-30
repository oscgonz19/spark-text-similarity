#!/usr/bin/env python3
"""
Run LSH experiments and generate results report.

Usage:
    python scripts/run_experiments.py [--num-docs N] [--output-dir DIR]
"""

import argparse
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyspark.sql import SparkSession

from src.data_generator import create_sample_rdd
from src.experiments import analyze_tradeoffs, format_results_table, results_to_csv, run_band_sweep
from src.pipeline import run_baseline


def main():
    parser = argparse.ArgumentParser(description="Run LSH experiments")
    parser.add_argument("--num-docs", type=int, default=50, help="Number of documents")
    parser.add_argument("--doc-length", type=int, default=100, help="Words per document")
    parser.add_argument("--num-similar", type=int, default=15, help="Number of similar pairs")
    parser.add_argument("--num-hashes", type=int, default=100, help="Signature length")
    parser.add_argument("--threshold", type=float, default=0.5, help="Similarity threshold")
    parser.add_argument("--output-dir", type=str, default="reports", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Create Spark session
    spark = SparkSession.builder \
        .appName("LSH-Experiments") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()

    sc = spark.sparkContext
    sc.setLogLevel("WARN")

    print(f"Generating corpus: {args.num_docs} documents, {args.num_similar} similar pairs...")

    # Generate synthetic corpus
    docs_rdd, expected_pairs = create_sample_rdd(
        sc,
        num_documents=args.num_docs,
        doc_length=args.doc_length,
        num_similar_pairs=args.num_similar,
        seed=args.seed
    )
    docs_rdd.cache()

    print("Computing ground truth (exact Jaccard)...")

    # Compute ground truth
    ground_truth = run_baseline(
        docs_rdd,
        shingle_size=3,
        char_level=True,
        threshold=args.threshold
    )
    ground_truth.cache()

    num_true_pairs = ground_truth.count()
    print(f"Ground truth: {num_true_pairs} pairs with similarity >= {args.threshold}")

    # Define band configurations to test
    # Use divisors of num_hashes
    band_values = [b for b in [1, 2, 4, 5, 10, 20, 25, 50, 100]
                   if args.num_hashes % b == 0]

    print(f"\nRunning experiments with bands: {band_values}")
    print("-" * 60)

    results = run_band_sweep(
        docs_rdd=docs_rdd,
        ground_truth_rdd=ground_truth,
        band_values=band_values,
        num_hashes=args.num_hashes,
        similarity_threshold=args.threshold
    )

    # Print results table
    print("\n" + format_results_table(results))

    # Analyze tradeoffs
    analysis = analyze_tradeoffs(results)
    print("\n=== Tradeoff Analysis ===")
    print(f"Best F1: {analysis['best_f1']['config']} -> F1={analysis['best_f1']['f1']:.3f}")
    print(f"Best Precision: {analysis['best_precision']['config']} -> P={analysis['best_precision']['precision']:.3f}")
    print(f"Best Recall: {analysis['best_recall']['config']} -> R={analysis['best_recall']['recall']:.3f}")
    print(f"Fastest: {analysis['fastest']['config']} -> {analysis['fastest']['runtime']:.2f}s")

    # Save results
    os.makedirs(args.output_dir, exist_ok=True)

    csv_path = os.path.join(args.output_dir, "experiment_results.csv")
    with open(csv_path, "w") as f:
        f.write(results_to_csv(results))
    print(f"\nResults saved to: {csv_path}")

    # Generate markdown report
    report_path = os.path.join(args.output_dir, "results.md")
    with open(report_path, "w") as f:
        f.write("# LSH Experiment Results\n\n")
        f.write("## Configuration\n\n")
        f.write(f"- Documents: {args.num_docs}\n")
        f.write(f"- Words per document: {args.doc_length}\n")
        f.write(f"- Similar pairs embedded: {args.num_similar}\n")
        f.write(f"- Signature length: {args.num_hashes}\n")
        f.write(f"- Similarity threshold: {args.threshold}\n")
        f.write(f"- Ground truth pairs: {num_true_pairs}\n\n")
        f.write("## Results\n\n")
        f.write(format_results_table(results))
        f.write("\n\n## Analysis\n\n")
        f.write(f"- **Best F1**: {analysis['best_f1']['config']} ")
        f.write(f"(P={analysis['best_f1']['precision']:.3f}, ")
        f.write(f"R={analysis['best_f1']['recall']:.3f}, ")
        f.write(f"F1={analysis['best_f1']['f1']:.3f})\n")
        f.write(f"- **Best Precision**: {analysis['best_precision']['config']} ")
        f.write(f"(P={analysis['best_precision']['precision']:.3f})\n")
        f.write(f"- **Best Recall**: {analysis['best_recall']['config']} ")
        f.write(f"(R={analysis['best_recall']['recall']:.3f})\n")
        f.write(f"- **Fastest**: {analysis['fastest']['config']} ")
        f.write(f"({analysis['fastest']['runtime']:.2f}s)\n")

    print(f"Report saved to: {report_path}")

    spark.stop()


if __name__ == "__main__":
    main()
