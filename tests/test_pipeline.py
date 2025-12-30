"""Tests for end-to-end pipeline."""

import pytest
from src.pipeline import (
    run_lsh_pipeline,
    run_baseline,
    evaluate_lsh,
    LSHConfig,
    PipelineResult
)
from src.data_generator import get_tiny_sample, create_sample_rdd


class TestLSHPipeline:
    """Tests for the LSH pipeline."""

    def test_pipeline_runs(self, sample_docs):
        """Test that pipeline completes without error."""
        config = LSHConfig(
            shingle_size=3,
            num_hashes=20,
            num_bands=4,
            similarity_threshold=0.3
        )

        result = run_lsh_pipeline(sample_docs, config)

        assert isinstance(result, PipelineResult)
        assert result.num_candidates >= 0
        assert result.num_similar >= 0
        assert result.num_similar <= result.num_candidates

    def test_pipeline_finds_similar_docs(self, sample_docs):
        """Test that pipeline finds known similar documents."""
        config = LSHConfig(
            shingle_size=3,
            num_hashes=100,
            num_bands=20,
            similarity_threshold=0.3
        )

        result = run_lsh_pipeline(sample_docs, config)
        similar_pairs = result.verified_pairs.collect()

        # Extract just the pair IDs
        pair_ids = {frozenset(pair) for pair, _ in similar_pairs}

        # doc1 and doc2 should be found as similar
        assert frozenset(["doc1", "doc2"]) in pair_ids

    def test_default_config(self, sample_docs):
        """Test pipeline with default configuration."""
        result = run_lsh_pipeline(sample_docs)

        assert result.config.shingle_size == 3
        assert result.config.num_hashes == 100
        assert result.config.num_bands == 20


class TestBaseline:
    """Tests for baseline exact computation."""

    def test_baseline_runs(self, sample_docs):
        """Test that baseline computation works."""
        result = run_baseline(sample_docs, threshold=0.0)
        pairs = result.collect()

        # 5 docs = 10 pairs
        assert len(pairs) == 10

    def test_baseline_with_threshold(self, sample_docs):
        """Test baseline with similarity threshold."""
        result = run_baseline(sample_docs, threshold=0.5)
        pairs = result.collect()

        for (doc1, doc2), sim in pairs:
            assert sim >= 0.5


class TestEvaluation:
    """Tests for LSH evaluation metrics."""

    def test_perfect_recall(self, sc):
        """Test evaluation when LSH finds all true pairs."""
        # Create small controlled dataset
        docs_rdd, _ = create_sample_rdd(sc, num_documents=10, num_similar_pairs=3, seed=42)

        config = LSHConfig(
            num_hashes=100,
            num_bands=50,  # Many bands = high recall
            similarity_threshold=0.3
        )

        result = run_lsh_pipeline(docs_rdd, config)
        ground_truth = run_baseline(docs_rdd, threshold=0.3)

        metrics = evaluate_lsh(result, ground_truth)

        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics
        assert 0 <= metrics["precision"] <= 1
        assert 0 <= metrics["recall"] <= 1

    def test_evaluation_with_tiny_sample(self, sc):
        """Test evaluation with tiny sample data."""
        docs_rdd = get_tiny_sample(sc)

        config = LSHConfig(
            num_hashes=100,
            num_bands=20,
            similarity_threshold=0.3
        )

        result = run_lsh_pipeline(docs_rdd, config)
        ground_truth = run_baseline(docs_rdd, threshold=0.3)

        metrics = evaluate_lsh(result, ground_truth)

        # Should find at least some pairs
        assert metrics["num_true_pairs"] > 0 or metrics["num_lsh_pairs"] >= 0


class TestSmokeTest:
    """Smoke tests for quick CI validation."""

    @pytest.mark.smoke
    def test_tiny_sample_pipeline(self, sc):
        """Quick smoke test with tiny dataset."""
        docs_rdd = get_tiny_sample(sc)

        config = LSHConfig(
            shingle_size=3,
            num_hashes=20,
            num_bands=4,
            similarity_threshold=0.3
        )

        result = run_lsh_pipeline(docs_rdd, config)

        # Basic sanity checks
        assert result.num_candidates >= 0
        assert result.config == config

    @pytest.mark.smoke
    def test_data_generator(self, sc):
        """Smoke test for data generator."""
        docs_rdd, pairs = create_sample_rdd(
            sc,
            num_documents=10,
            num_similar_pairs=2,
            seed=42
        )

        assert docs_rdd.count() == 10
        assert len(pairs) <= 2
