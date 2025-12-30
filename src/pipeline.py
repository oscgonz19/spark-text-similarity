"""
End-to-end pipeline: Shingling -> MinHash -> LSH -> Candidate Pairs -> Verify.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from pyspark.rdd import RDD

from .jaccard import compute_all_pairs_jaccard, compute_pairwise_jaccard_distributed
from .lsh import lsh_candidates
from .minhash import compute_signatures_rdd
from .shingling import create_shingle_rdd, get_shingle_vocabulary, shingles_to_ids


@dataclass
class LSHConfig:
    """Configuration for LSH pipeline."""

    shingle_size: int = 3
    char_level: bool = True
    num_hashes: int = 100
    num_bands: int = 20
    similarity_threshold: float = 0.5
    seed: int = 42


@dataclass
class PipelineResult:
    """Results from running the LSH pipeline."""

    candidate_pairs: RDD
    verified_pairs: RDD
    num_candidates: int
    num_similar: int
    config: LSHConfig


def run_lsh_pipeline(docs_rdd: RDD, config: Optional[LSHConfig] = None) -> PipelineResult:
    """
    Run the complete LSH pipeline.

    Args:
        docs_rdd: RDD of (doc_id, text) tuples
        config: LSH configuration parameters

    Returns:
        PipelineResult with candidate and verified similar pairs
    """
    if config is None:
        config = LSHConfig()

    # Step 1: Shingling
    shingles_rdd = create_shingle_rdd(docs_rdd, k=config.shingle_size, char_level=config.char_level)

    # Step 2: Build vocabulary and convert to IDs
    vocab = get_shingle_vocabulary(shingles_rdd)
    shingle_ids_rdd = shingles_to_ids(shingles_rdd, vocab)

    # Step 3: Compute MinHash signatures
    signatures_rdd = compute_signatures_rdd(
        shingle_ids_rdd, num_hashes=config.num_hashes, seed=config.seed
    )

    # Step 4: LSH to find candidate pairs
    candidate_pairs = lsh_candidates(signatures_rdd, config.num_bands)
    num_candidates = candidate_pairs.count()

    # Step 5: Verify candidates with exact Jaccard
    verified_pairs = compute_pairwise_jaccard_distributed(shingles_rdd, candidate_pairs).filter(
        lambda x: x[1] >= config.similarity_threshold
    )

    num_similar = verified_pairs.count()

    return PipelineResult(
        candidate_pairs=candidate_pairs,
        verified_pairs=verified_pairs,
        num_candidates=num_candidates,
        num_similar=num_similar,
        config=config,
    )


def run_baseline(
    docs_rdd: RDD, shingle_size: int = 3, char_level: bool = True, threshold: float = 0.5
) -> RDD:
    """
    Run baseline exact Jaccard computation for all pairs.

    Args:
        docs_rdd: RDD of (doc_id, text) tuples
        shingle_size: Size of shingles
        char_level: Character or word level shingling
        threshold: Minimum similarity threshold

    Returns:
        RDD of ((doc_id_1, doc_id_2), similarity) for pairs above threshold
    """
    shingles_rdd = create_shingle_rdd(docs_rdd, k=shingle_size, char_level=char_level)
    return compute_all_pairs_jaccard(shingles_rdd, threshold)


def evaluate_lsh(lsh_result: PipelineResult, ground_truth_rdd: RDD) -> Dict[str, float]:
    """
    Evaluate LSH performance against ground truth.

    Args:
        lsh_result: Results from LSH pipeline
        ground_truth_rdd: RDD of ((doc_id_1, doc_id_2), similarity) ground truth

    Returns:
        Dictionary with precision, recall, and F1 metrics
    """
    # Get sets of pairs
    lsh_pairs = set(lsh_result.verified_pairs.map(lambda x: x[0]).collect())
    true_pairs = set(ground_truth_rdd.map(lambda x: x[0]).collect())

    # Calculate metrics
    if not lsh_pairs:
        precision = 0.0
    else:
        true_positives = len(lsh_pairs & true_pairs)
        precision = true_positives / len(lsh_pairs)

    if not true_pairs:
        recall = 1.0  # No ground truth = nothing to recall
    else:
        true_positives = len(lsh_pairs & true_pairs)
        recall = true_positives / len(true_pairs)

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": len(lsh_pairs & true_pairs),
        "false_positives": len(lsh_pairs - true_pairs),
        "false_negatives": len(true_pairs - lsh_pairs),
        "num_lsh_pairs": len(lsh_pairs),
        "num_true_pairs": len(true_pairs),
    }
