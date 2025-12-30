#!/usr/bin/env python3
"""
Run LSH pipeline on input documents.

Usage:
    python scripts/run_pipeline.py --input data/sample/docs.txt --output output/
    python scripts/run_pipeline.py --demo  # Run with built-in demo data
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyspark.sql import SparkSession

from src.data_generator import create_sample_rdd, get_tiny_sample
from src.pipeline import LSHConfig, run_lsh_pipeline


def load_documents(spark, input_path: str):
    """Load documents from text file (one doc per line, format: id<TAB>text)."""
    sc = spark.sparkContext
    return sc.textFile(input_path).map(lambda line: tuple(line.split("\t", 1)))


def main():
    parser = argparse.ArgumentParser(description="Run LSH similarity pipeline")
    parser.add_argument("--input", type=str, help="Input file (id<TAB>text per line)")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run with demo data")
    parser.add_argument("--bands", type=int, default=20, help="Number of LSH bands")
    parser.add_argument("--hashes", type=int, default=100, help="Signature length")
    parser.add_argument("--threshold", type=float, default=0.5, help="Similarity threshold")
    parser.add_argument("--shingle-size", type=int, default=3, help="Shingle size")
    args = parser.parse_args()

    spark = SparkSession.builder \
        .appName("LSH-Pipeline") \
        .master("local[*]") \
        .getOrCreate()

    sc = spark.sparkContext
    sc.setLogLevel("WARN")

    # Load data
    if args.demo:
        print("Running with demo data...")
        docs_rdd = get_tiny_sample(sc)
    elif args.input:
        print(f"Loading documents from: {args.input}")
        docs_rdd = load_documents(spark, args.input)
    else:
        print("Generating sample corpus...")
        docs_rdd, _ = create_sample_rdd(sc, num_documents=30, num_similar_pairs=10)

    num_docs = docs_rdd.count()
    print(f"Loaded {num_docs} documents")

    # Configure and run pipeline
    config = LSHConfig(
        shingle_size=args.shingle_size,
        num_hashes=args.hashes,
        num_bands=args.bands,
        similarity_threshold=args.threshold
    )

    print("\nRunning LSH pipeline:")
    print(f"  - Shingle size: {config.shingle_size}")
    print(f"  - Signature length: {config.num_hashes}")
    print(f"  - Bands: {config.num_bands} (rows per band: {config.num_hashes // config.num_bands})")
    print(f"  - Similarity threshold: {config.similarity_threshold}")

    result = run_lsh_pipeline(docs_rdd, config)

    print("\nResults:")
    print(f"  - Candidate pairs: {result.num_candidates}")
    print(f"  - Similar pairs (>= {args.threshold}): {result.num_similar}")

    # Save results
    os.makedirs(args.output, exist_ok=True)

    similar_pairs = result.verified_pairs.collect()
    output_path = os.path.join(args.output, "similar_pairs.txt")

    with open(output_path, "w") as f:
        f.write("doc_id_1\tdoc_id_2\tsimilarity\n")
        for (doc1, doc2), sim in sorted(similar_pairs, key=lambda x: -x[1]):
            f.write(f"{doc1}\t{doc2}\t{sim:.4f}\n")

    print(f"\nSimilar pairs saved to: {output_path}")

    # Print top pairs
    if similar_pairs:
        print("\nTop similar pairs:")
        for (doc1, doc2), sim in sorted(similar_pairs, key=lambda x: -x[1])[:10]:
            print(f"  {doc1} <-> {doc2}: {sim:.4f}")

    spark.stop()


if __name__ == "__main__":
    main()
