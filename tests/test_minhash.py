"""Tests for MinHash module."""

import pytest

from src.minhash import (
    compute_signatures_rdd,
    create_hash_functions,
    estimate_similarity,
    minhash_signature,
)
from src.shingling import create_shingle_rdd, get_shingle_vocabulary, shingles_to_ids


class TestHashFunctions:
    """Tests for hash function generation."""

    def test_hash_function_count(self):
        """Test correct number of hash functions generated."""
        hash_funcs = create_hash_functions(100, seed=42)
        assert len(hash_funcs) == 100

    def test_hash_function_reproducibility(self):
        """Test that same seed gives same functions."""
        funcs1 = create_hash_functions(10, seed=42)
        funcs2 = create_hash_functions(10, seed=42)
        assert funcs1 == funcs2

    def test_different_seeds_differ(self):
        """Test that different seeds give different functions."""
        funcs1 = create_hash_functions(10, seed=42)
        funcs2 = create_hash_functions(10, seed=123)
        assert funcs1 != funcs2


class TestMinHashSignature:
    """Tests for MinHash signature computation."""

    def test_signature_length(self):
        """Test signature has correct length."""
        shingle_ids = {1, 2, 3, 4, 5}
        hash_params = create_hash_functions(50)
        sig = minhash_signature(shingle_ids, hash_params)
        assert len(sig) == 50

    def test_empty_set_signature(self):
        """Test signature for empty set."""
        hash_params = create_hash_functions(10)
        sig = minhash_signature(set(), hash_params)
        assert len(sig) == 10
        # Should be max values for empty set
        assert all(v > 0 for v in sig)

    def test_signature_deterministic(self):
        """Test that same input gives same signature."""
        shingle_ids = {1, 2, 3}
        hash_params = create_hash_functions(20, seed=42)
        sig1 = minhash_signature(shingle_ids, hash_params)
        sig2 = minhash_signature(shingle_ids, hash_params)
        assert sig1 == sig2

    def test_identical_sets_same_signature(self):
        """Identical sets should have identical signatures."""
        set_a = {1, 2, 3, 4, 5}
        set_b = {1, 2, 3, 4, 5}
        hash_params = create_hash_functions(100, seed=42)
        sig_a = minhash_signature(set_a, hash_params)
        sig_b = minhash_signature(set_b, hash_params)
        assert sig_a == sig_b


class TestEstimateSimilarity:
    """Tests for similarity estimation from signatures."""

    def test_identical_signatures(self):
        """Identical signatures should give similarity 1.0."""
        sig = [1, 2, 3, 4, 5]
        assert estimate_similarity(sig, sig) == 1.0

    def test_completely_different_signatures(self):
        """Completely different signatures should give similarity 0.0."""
        sig_a = [1, 2, 3, 4, 5]
        sig_b = [6, 7, 8, 9, 10]
        assert estimate_similarity(sig_a, sig_b) == 0.0

    def test_partial_match(self):
        """Test signatures with partial match."""
        sig_a = [1, 2, 3, 4, 5]
        sig_b = [1, 2, 6, 7, 8]
        # 2 out of 5 match
        assert estimate_similarity(sig_a, sig_b) == 0.4

    def test_length_mismatch_raises(self):
        """Different length signatures should raise error."""
        sig_a = [1, 2, 3]
        sig_b = [1, 2]
        with pytest.raises(ValueError):
            estimate_similarity(sig_a, sig_b)


class TestComputeSignaturesRDD:
    """Tests for RDD signature computation."""

    def test_compute_signatures(self, sample_docs):
        """Test computing signatures for documents."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3)
        vocab = get_shingle_vocabulary(shingles_rdd)
        ids_rdd = shingles_to_ids(shingles_rdd, vocab)

        signatures_rdd = compute_signatures_rdd(ids_rdd, num_hashes=50)
        results = dict(signatures_rdd.collect())

        assert len(results) == 5
        for doc_id, sig in results.items():
            assert len(sig) == 50

    def test_similar_docs_have_similar_signatures(self, sample_docs):
        """Similar documents should have more matching hash values."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3)
        vocab = get_shingle_vocabulary(shingles_rdd)
        ids_rdd = shingles_to_ids(shingles_rdd, vocab)

        signatures_rdd = compute_signatures_rdd(ids_rdd, num_hashes=100, seed=42)
        sigs = dict(signatures_rdd.collect())

        # doc1 and doc2 are similar
        sim_12 = estimate_similarity(sigs["doc1"], sigs["doc2"])
        # doc1 and doc3 are different
        sim_13 = estimate_similarity(sigs["doc1"], sigs["doc3"])

        assert sim_12 > sim_13
