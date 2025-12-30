"""
Locality-Sensitive Hashing (LSH) module: Find candidate pairs efficiently.

LSH divides MinHash signatures into bands. Documents that hash to the same
bucket in ANY band become candidate pairs.

Key parameters:
- b (bands): More bands = higher recall, more false positives
- r (rows per band): More rows = higher precision, more false negatives
- n = b * r (total signature length)

Probability of becoming candidates ≈ 1 - (1 - s^r)^b where s is true similarity.
"""

from typing import List, Tuple

from pyspark.rdd import RDD


def split_into_bands(
    signature: List[int],
    num_bands: int
) -> List[Tuple[int, Tuple]]:
    """
    Split a signature into bands.

    Args:
        signature: MinHash signature
        num_bands: Number of bands

    Returns:
        List of (band_index, band_values) tuples
    """
    sig_length = len(signature)
    rows_per_band = sig_length // num_bands

    bands = []
    for i in range(num_bands):
        start = i * rows_per_band
        end = start + rows_per_band
        band_values = tuple(signature[start:end])
        bands.append((i, band_values))

    return bands


def lsh_candidates(
    signatures_rdd: RDD,
    num_bands: int
) -> RDD:
    """
    Find candidate pairs using LSH banding.

    Args:
        signatures_rdd: RDD of (doc_id, signature) tuples
        num_bands: Number of bands to use

    Returns:
        RDD of (doc_id_1, doc_id_2) candidate pairs (deduplicated)
    """
    # Step 1: Create (band_idx, band_hash) -> doc_id mappings
    def emit_band_buckets(doc_sig):
        doc_id, signature = doc_sig
        bands = split_into_bands(signature, num_bands)
        for band_idx, band_values in bands:
            # Use (band_idx, band_values) as bucket key
            bucket_key = (band_idx, band_values)
            yield (bucket_key, doc_id)

    band_buckets = signatures_rdd.flatMap(emit_band_buckets)

    # Step 2: Group documents by bucket
    buckets_grouped = band_buckets.groupByKey().mapValues(list)

    # Step 3: Generate candidate pairs from each bucket
    def generate_pairs(bucket_docs):
        bucket_key, doc_ids = bucket_docs
        doc_ids = list(set(doc_ids))  # Remove duplicates within bucket
        pairs = []
        for i in range(len(doc_ids)):
            for j in range(i + 1, len(doc_ids)):
                # Ensure consistent ordering
                pair = tuple(sorted([doc_ids[i], doc_ids[j]]))
                pairs.append(pair)
        return pairs

    candidate_pairs = (
        buckets_grouped
        .flatMap(generate_pairs)
        .distinct()  # Remove duplicate pairs across bands
    )

    return candidate_pairs


def lsh_threshold(num_bands: int, rows_per_band: int) -> float:
    """
    Compute the approximate similarity threshold for LSH.

    This is the similarity value where P(candidate) ≈ 0.5.

    Args:
        num_bands: Number of bands
        rows_per_band: Rows per band

    Returns:
        Approximate threshold similarity
    """
    # Threshold ≈ (1/b)^(1/r)
    return (1 / num_bands) ** (1 / rows_per_band)


def candidate_probability(similarity: float, num_bands: int, rows_per_band: int) -> float:
    """
    Compute probability that two documents become candidates given their similarity.

    P(candidate) = 1 - (1 - s^r)^b

    Args:
        similarity: True Jaccard similarity
        num_bands: Number of bands
        rows_per_band: Rows per band

    Returns:
        Probability of becoming candidates
    """
    if similarity <= 0:
        return 0.0
    if similarity >= 1:
        return 1.0

    # P(at least one band matches) = 1 - P(no band matches)
    # P(no band matches) = (1 - P(band matches))^b
    # P(band matches) = s^r (all r rows in band must match)
    prob_band_match = similarity ** rows_per_band
    prob_no_band_match = (1 - prob_band_match) ** num_bands
    return 1 - prob_no_band_match


def find_optimal_params(
    target_threshold: float,
    signature_length: int = 100
) -> Tuple[int, int]:
    """
    Find optimal (bands, rows) for a target similarity threshold.

    Args:
        target_threshold: Desired similarity threshold
        signature_length: Total signature length (must be divisible by bands)

    Returns:
        Tuple of (num_bands, rows_per_band)
    """
    best_params = (1, signature_length)
    best_diff = float('inf')

    for b in range(1, signature_length + 1):
        if signature_length % b != 0:
            continue
        r = signature_length // b
        threshold = lsh_threshold(b, r)
        diff = abs(threshold - target_threshold)
        if diff < best_diff:
            best_diff = diff
            best_params = (b, r)

    return best_params
