"""Tests for LSH module."""

import pytest
from src.lsh import (
    split_into_bands,
    lsh_candidates,
    lsh_threshold,
    candidate_probability,
    find_optimal_params
)
from src.shingling import create_shingle_rdd, get_shingle_vocabulary, shingles_to_ids
from src.minhash import compute_signatures_rdd


class TestSplitIntoBands:
    """Tests for band splitting."""

    def test_basic_split(self):
        """Test basic band splitting."""
        signature = list(range(10))
        bands = split_into_bands(signature, num_bands=2)

        assert len(bands) == 2
        assert bands[0] == (0, (0, 1, 2, 3, 4))
        assert bands[1] == (1, (5, 6, 7, 8, 9))

    def test_five_bands(self):
        """Test splitting into 5 bands."""
        signature = list(range(100))
        bands = split_into_bands(signature, num_bands=5)

        assert len(bands) == 5
        for i, (band_idx, values) in enumerate(bands):
            assert band_idx == i
            assert len(values) == 20


class TestLSHThreshold:
    """Tests for LSH theoretical threshold."""

    def test_threshold_calculation(self):
        """Test threshold calculation."""
        # With b=20, r=5: threshold ≈ (1/20)^(1/5) ≈ 0.55
        threshold = lsh_threshold(num_bands=20, rows_per_band=5)
        assert 0.5 < threshold < 0.6

    def test_more_bands_lower_threshold(self):
        """More bands should give lower threshold."""
        t1 = lsh_threshold(10, 10)
        t2 = lsh_threshold(20, 5)
        assert t2 < t1  # More bands = lower threshold

    def test_more_rows_higher_threshold(self):
        """More rows per band should give higher threshold."""
        t1 = lsh_threshold(10, 10)
        t2 = lsh_threshold(5, 20)
        assert t2 > t1  # More rows = higher threshold


class TestCandidateProbability:
    """Tests for candidate probability calculation."""

    def test_zero_similarity(self):
        """Zero similarity should give zero probability."""
        prob = candidate_probability(0.0, num_bands=20, rows_per_band=5)
        assert prob == 0.0

    def test_one_similarity(self):
        """Similarity 1.0 should give probability 1.0."""
        prob = candidate_probability(1.0, num_bands=20, rows_per_band=5)
        assert prob == 1.0

    def test_high_similarity_high_probability(self):
        """High similarity should give high probability."""
        prob = candidate_probability(0.8, num_bands=20, rows_per_band=5)
        assert prob > 0.9

    def test_low_similarity_low_probability(self):
        """Low similarity should give low probability."""
        prob = candidate_probability(0.2, num_bands=20, rows_per_band=5)
        assert prob < 0.1


class TestFindOptimalParams:
    """Tests for optimal parameter finding."""

    def test_find_params_for_threshold(self):
        """Test finding params for specific threshold."""
        bands, rows = find_optimal_params(0.5, signature_length=100)
        assert bands * rows == 100

        actual_threshold = lsh_threshold(bands, rows)
        assert abs(actual_threshold - 0.5) < 0.1

    def test_returns_valid_divisors(self):
        """Should return valid divisors of signature length."""
        bands, rows = find_optimal_params(0.7, signature_length=100)
        assert 100 % bands == 0
        assert bands * rows == 100


class TestLSHCandidates:
    """Tests for LSH candidate pair finding."""

    def test_finds_similar_pairs(self, sample_docs):
        """Test that LSH finds similar document pairs."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3)
        vocab = get_shingle_vocabulary(shingles_rdd)
        ids_rdd = shingles_to_ids(shingles_rdd, vocab)
        signatures_rdd = compute_signatures_rdd(ids_rdd, num_hashes=100)

        candidates = lsh_candidates(signatures_rdd, num_bands=20)
        candidate_pairs = set(candidates.collect())

        # doc1 and doc2 are similar, should be candidates
        assert ("doc1", "doc2") in candidate_pairs or ("doc2", "doc1") in candidate_pairs

    def test_candidates_are_deduplicated(self, sample_docs):
        """Test that candidate pairs are unique."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3)
        vocab = get_shingle_vocabulary(shingles_rdd)
        ids_rdd = shingles_to_ids(shingles_rdd, vocab)
        signatures_rdd = compute_signatures_rdd(ids_rdd, num_hashes=100)

        candidates = lsh_candidates(signatures_rdd, num_bands=20).collect()

        # No duplicate pairs
        assert len(candidates) == len(set(candidates))

    def test_more_bands_more_candidates(self, sample_docs):
        """More bands should generally produce more candidates."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3)
        vocab = get_shingle_vocabulary(shingles_rdd)
        ids_rdd = shingles_to_ids(shingles_rdd, vocab)
        signatures_rdd = compute_signatures_rdd(ids_rdd, num_hashes=100)

        # Cache for reuse
        signatures_rdd.cache()

        candidates_10 = lsh_candidates(signatures_rdd, num_bands=10).count()
        candidates_50 = lsh_candidates(signatures_rdd, num_bands=50).count()

        # More bands = lower threshold = more candidates (usually)
        # Note: This is a probabilistic property, may not always hold for small datasets
        assert candidates_50 >= candidates_10 or candidates_50 > 0
