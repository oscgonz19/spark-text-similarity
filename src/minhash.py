"""
MinHash module: Generate compact signatures that preserve Jaccard similarity.

The probability that MinHash values match equals the Jaccard similarity:
P(h(A) = h(B)) = Jaccard(A, B)
"""

import random
from typing import List, Set, Tuple

from pyspark.rdd import RDD

# Large prime for hash functions (Mersenne prime)
LARGE_PRIME = 2147483647  # 2^31 - 1


def create_hash_functions(num_hashes: int, seed: int = 42) -> List[Tuple[int, int]]:
    """
    Generate hash function parameters (a, b) for h(x) = (ax + b) mod p.

    Args:
        num_hashes: Number of hash functions to generate
        seed: Random seed for reproducibility

    Returns:
        List of (a, b) tuples for hash functions
    """
    random.seed(seed)
    hash_funcs = []

    for _ in range(num_hashes):
        a = random.randint(1, LARGE_PRIME - 1)
        b = random.randint(0, LARGE_PRIME - 1)
        hash_funcs.append((a, b))

    return hash_funcs


def minhash_signature(
    shingle_ids: Set[int],
    hash_params: List[Tuple[int, int]],
    num_buckets: int = LARGE_PRIME
) -> List[int]:
    """
    Compute MinHash signature for a set of shingle IDs.

    Args:
        shingle_ids: Set of integer shingle IDs
        hash_params: List of (a, b) hash function parameters
        num_buckets: Modulo for hash function

    Returns:
        MinHash signature as list of integers
    """
    if not shingle_ids:
        # Return max values for empty sets
        return [LARGE_PRIME] * len(hash_params)

    signature = []

    for a, b in hash_params:
        min_hash = LARGE_PRIME
        for shingle_id in shingle_ids:
            # h(x) = (ax + b) mod p
            hash_val = (a * shingle_id + b) % num_buckets
            min_hash = min(min_hash, hash_val)
        signature.append(min_hash)

    return signature


def compute_signatures_rdd(
    shingle_ids_rdd: RDD,
    num_hashes: int = 100,
    seed: int = 42
) -> RDD:
    """
    Compute MinHash signatures for all documents.

    Args:
        shingle_ids_rdd: RDD of (doc_id, set of shingle integer IDs)
        num_hashes: Number of hash functions (signature length)
        seed: Random seed for hash function generation

    Returns:
        RDD of (doc_id, signature_list)
    """
    # Generate hash functions and broadcast
    hash_params = create_hash_functions(num_hashes, seed)
    hash_params_broadcast = shingle_ids_rdd.context.broadcast(hash_params)

    def compute_signature(doc_shingles):
        doc_id, shingle_ids = doc_shingles
        sig = minhash_signature(shingle_ids, hash_params_broadcast.value)
        return (doc_id, sig)

    return shingle_ids_rdd.map(compute_signature)


def estimate_similarity(sig_a: List[int], sig_b: List[int]) -> float:
    """
    Estimate Jaccard similarity from MinHash signatures.

    The estimate is the fraction of hash positions that match.

    Args:
        sig_a: First signature
        sig_b: Second signature

    Returns:
        Estimated Jaccard similarity
    """
    if len(sig_a) != len(sig_b):
        raise ValueError("Signatures must have same length")

    if not sig_a:
        return 0.0

    matches = sum(1 for a, b in zip(sig_a, sig_b) if a == b)
    return matches / len(sig_a)
