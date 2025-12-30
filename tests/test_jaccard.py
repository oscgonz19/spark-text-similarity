"""Tests for Jaccard similarity module."""

import pytest
from src.jaccard import (
    jaccard_similarity,
    compute_all_pairs_jaccard,
    find_similar_pairs
)
from src.shingling import create_shingle_rdd


class TestJaccardSimilarity:
    """Tests for jaccard_similarity function."""

    def test_identical_sets(self):
        """Identical sets should have similarity 1.0."""
        set_a = {1, 2, 3}
        set_b = {1, 2, 3}
        assert jaccard_similarity(set_a, set_b) == 1.0

    def test_disjoint_sets(self):
        """Disjoint sets should have similarity 0.0."""
        set_a = {1, 2, 3}
        set_b = {4, 5, 6}
        assert jaccard_similarity(set_a, set_b) == 0.0

    def test_partial_overlap(self):
        """Test sets with partial overlap."""
        set_a = {1, 2, 3}
        set_b = {2, 3, 4}
        # Intersection: {2, 3} = 2, Union: {1, 2, 3, 4} = 4
        assert jaccard_similarity(set_a, set_b) == 0.5

    def test_empty_sets(self):
        """Two empty sets should have similarity 1.0."""
        assert jaccard_similarity(set(), set()) == 1.0

    def test_one_empty_set(self):
        """One empty set should give similarity 0.0."""
        assert jaccard_similarity({1, 2}, set()) == 0.0
        assert jaccard_similarity(set(), {1, 2}) == 0.0

    def test_subset(self):
        """Test when one set is subset of another."""
        set_a = {1, 2}
        set_b = {1, 2, 3, 4}
        # Intersection: 2, Union: 4
        assert jaccard_similarity(set_a, set_b) == 0.5


class TestAllPairsJaccard:
    """Tests for all-pairs Jaccard computation."""

    def test_all_pairs_computation(self, sample_docs):
        """Test computing all pairs Jaccard."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3)
        pairs_rdd = compute_all_pairs_jaccard(shingles_rdd, threshold=0.0)

        pairs = pairs_rdd.collect()

        # 5 docs = 10 pairs
        assert len(pairs) == 10

        # All similarities should be between 0 and 1
        for (doc1, doc2), sim in pairs:
            assert 0.0 <= sim <= 1.0

    def test_threshold_filtering(self, sample_docs):
        """Test that threshold filters low similarity pairs."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3)

        all_pairs = compute_all_pairs_jaccard(shingles_rdd, threshold=0.0).collect()
        high_pairs = compute_all_pairs_jaccard(shingles_rdd, threshold=0.5).collect()

        assert len(high_pairs) <= len(all_pairs)
        for (doc1, doc2), sim in high_pairs:
            assert sim >= 0.5

    def test_similar_docs_detected(self, sample_docs):
        """Test that similar documents are detected."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3)
        pairs = find_similar_pairs(shingles_rdd, threshold=0.3).collect()

        # doc1 and doc2 should be detected as similar
        pair_set = {frozenset(pair) for pair, _ in pairs}
        assert frozenset(["doc1", "doc2"]) in pair_set


class TestIdenticalDocs:
    """Tests for edge cases with identical documents."""

    def test_identical_docs_similarity(self, identical_docs):
        """Identical documents should have similarity 1.0."""
        shingles_rdd = create_shingle_rdd(identical_docs, k=3)
        pairs = compute_all_pairs_jaccard(shingles_rdd, threshold=0.0).collect()

        assert len(pairs) == 1
        (doc1, doc2), sim = pairs[0]
        assert sim == 1.0
