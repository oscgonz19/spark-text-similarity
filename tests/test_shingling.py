"""Tests for shingling module."""

from src.shingling import (
    create_shingle_rdd,
    get_shingle_vocabulary,
    shingles_to_ids,
    text_to_shingles,
)


class TestTextToShingles:
    """Tests for text_to_shingles function."""

    def test_basic_char_shingles(self):
        """Test character-level 3-shingles."""
        text = "abcde"
        shingles = text_to_shingles(text, k=3, char_level=True)
        assert shingles == {"abc", "bcd", "cde"}

    def test_basic_word_shingles(self):
        """Test word-level 2-shingles."""
        text = "the quick brown fox"
        shingles = text_to_shingles(text, k=2, char_level=False)
        assert shingles == {"the quick", "quick brown", "brown fox"}

    def test_short_text(self):
        """Test text shorter than k."""
        text = "ab"
        shingles = text_to_shingles(text, k=3, char_level=True)
        assert shingles == {"ab"}

    def test_empty_text(self):
        """Test empty text."""
        shingles = text_to_shingles("", k=3, char_level=True)
        assert shingles == set()

    def test_case_insensitive(self):
        """Test that shingling is case-insensitive."""
        text1 = "ABC"
        text2 = "abc"
        assert text_to_shingles(text1, k=2) == text_to_shingles(text2, k=2)

    def test_whitespace_handling(self):
        """Test whitespace is preserved in shingles."""
        text = "a b"
        shingles = text_to_shingles(text, k=3, char_level=True)
        assert "a b" in shingles


class TestShingleRDD:
    """Tests for RDD shingling operations."""

    def test_create_shingle_rdd(self, sample_docs):
        """Test creating shingle RDD from documents."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3, char_level=True)
        results = dict(shingles_rdd.collect())

        assert "doc1" in results
        assert isinstance(results["doc1"], set)
        assert len(results["doc1"]) > 0

    def test_vocabulary_creation(self, sample_docs):
        """Test vocabulary building from shingles."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3, char_level=True)
        vocab = get_shingle_vocabulary(shingles_rdd)

        assert isinstance(vocab, dict)
        assert len(vocab) > 0
        # All values should be unique integers
        assert len(set(vocab.values())) == len(vocab)

    def test_shingles_to_ids(self, sample_docs):
        """Test converting shingles to integer IDs."""
        shingles_rdd = create_shingle_rdd(sample_docs, k=3)
        vocab = get_shingle_vocabulary(shingles_rdd)
        ids_rdd = shingles_to_ids(shingles_rdd, vocab)

        results = dict(ids_rdd.collect())
        assert "doc1" in results
        assert all(isinstance(i, int) for i in results["doc1"])
