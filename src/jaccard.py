"""
Jaccard similarity: Exact computation for baseline comparison.

Jaccard(A, B) = |A ∩ B| / |A ∪ B|
"""

from typing import Set, List, Tuple
from pyspark.rdd import RDD
from itertools import combinations


def jaccard_similarity(set_a: Set, set_b: Set) -> float:
    """
    Compute exact Jaccard similarity between two sets.

    Args:
        set_a: First set
        set_b: Second set

    Returns:
        Jaccard similarity in [0, 1]
    """
    if not set_a and not set_b:
        return 1.0  # Two empty sets are identical
    if not set_a or not set_b:
        return 0.0

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    return intersection / union if union > 0 else 0.0


def compute_all_pairs_jaccard(
    shingles_rdd: RDD,
    threshold: float = 0.0
) -> RDD:
    """
    Compute Jaccard similarity for all document pairs (brute force).

    WARNING: O(n^2) complexity. Only use for small datasets or validation.

    Args:
        shingles_rdd: RDD of (doc_id, shingle_set) tuples
        threshold: Minimum similarity to include in output

    Returns:
        RDD of ((doc_id_1, doc_id_2), jaccard_similarity)
    """
    # Collect all documents (only viable for small datasets)
    docs = shingles_rdd.collect()

    # Generate all pairs with similarity
    pairs = []
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            doc_id_1, shingles_1 = docs[i]
            doc_id_2, shingles_2 = docs[j]
            sim = jaccard_similarity(shingles_1, shingles_2)
            if sim >= threshold:
                pairs.append(((doc_id_1, doc_id_2), sim))

    return shingles_rdd.context.parallelize(pairs)


def compute_pairwise_jaccard_distributed(
    shingles_rdd: RDD,
    candidate_pairs: RDD,
) -> RDD:
    """
    Compute Jaccard similarity only for candidate pairs (from LSH).

    Args:
        shingles_rdd: RDD of (doc_id, shingle_set) tuples
        candidate_pairs: RDD of (doc_id_1, doc_id_2) candidate pairs

    Returns:
        RDD of ((doc_id_1, doc_id_2), jaccard_similarity)
    """
    # Create lookup dict broadcasted
    docs_dict = dict(shingles_rdd.collect())
    docs_broadcast = shingles_rdd.context.broadcast(docs_dict)

    def compute_pair_similarity(pair):
        doc_id_1, doc_id_2 = pair
        docs = docs_broadcast.value
        if doc_id_1 in docs and doc_id_2 in docs:
            sim = jaccard_similarity(docs[doc_id_1], docs[doc_id_2])
            return ((doc_id_1, doc_id_2), sim)
        return ((doc_id_1, doc_id_2), 0.0)

    return candidate_pairs.map(compute_pair_similarity)


def find_similar_pairs(
    shingles_rdd: RDD,
    threshold: float = 0.5
) -> RDD:
    """
    Find all document pairs with Jaccard similarity >= threshold.

    Args:
        shingles_rdd: RDD of (doc_id, shingle_set) tuples
        threshold: Minimum similarity threshold

    Returns:
        RDD of ((doc_id_1, doc_id_2), jaccard_similarity)
    """
    return compute_all_pairs_jaccard(shingles_rdd, threshold)
