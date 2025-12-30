"""
Synthetic dataset generator for testing document similarity.

Generates documents with controlled similarity levels for benchmarking.
All generated content is original and released under CC0 (public domain).
"""

import random
import string
from typing import List, Tuple, Optional
from pyspark import SparkContext
from pyspark.rdd import RDD


# Base vocabulary for synthetic documents (common English words)
BASE_VOCABULARY = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
    "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
    "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only", "come",
    "its", "over", "think", "also", "back", "after", "use", "two", "how",
    "our", "work", "first", "well", "way", "even", "new", "want", "because",
    "any", "these", "give", "day", "most", "us", "data", "system", "process",
    "analysis", "method", "result", "study", "research", "model", "approach",
    "algorithm", "function", "value", "set", "number", "problem", "solution"
]


def generate_random_document(
    num_words: int = 50,
    vocabulary: List[str] = None,
    seed: Optional[int] = None
) -> str:
    """
    Generate a random document from vocabulary.

    Args:
        num_words: Number of words in document
        vocabulary: List of words to sample from
        seed: Random seed for reproducibility

    Returns:
        Generated document text
    """
    if seed is not None:
        random.seed(seed)

    if vocabulary is None:
        vocabulary = BASE_VOCABULARY

    words = [random.choice(vocabulary) for _ in range(num_words)]
    return " ".join(words)


def generate_similar_document(
    base_document: str,
    similarity: float,
    vocabulary: List[str] = None,
    seed: Optional[int] = None
) -> str:
    """
    Generate a document with approximate target similarity to base.

    Args:
        base_document: Source document
        similarity: Target Jaccard similarity (0-1)
        vocabulary: Vocabulary for replacement words
        seed: Random seed

    Returns:
        Document with approximately target similarity
    """
    if seed is not None:
        random.seed(seed)

    if vocabulary is None:
        vocabulary = BASE_VOCABULARY

    words = base_document.split()
    num_to_replace = int(len(words) * (1 - similarity))

    # Replace random positions
    positions = random.sample(range(len(words)), min(num_to_replace, len(words)))
    for pos in positions:
        words[pos] = random.choice(vocabulary)

    return " ".join(words)


def generate_document_pairs(
    num_pairs: int,
    similarity_levels: List[float] = None,
    doc_length: int = 50,
    seed: int = 42
) -> List[Tuple[str, str, str, float]]:
    """
    Generate pairs of documents with known similarities.

    Args:
        num_pairs: Number of document pairs to generate
        similarity_levels: List of similarity levels to use
        doc_length: Number of words per document
        seed: Random seed

    Returns:
        List of (doc_id_1, doc_id_2, doc_text_1, doc_text_2, target_similarity)
    """
    if similarity_levels is None:
        similarity_levels = [0.2, 0.4, 0.6, 0.8, 0.9]

    random.seed(seed)
    pairs = []

    for i in range(num_pairs):
        sim = random.choice(similarity_levels)
        base_doc = generate_random_document(doc_length, seed=seed + i * 2)
        similar_doc = generate_similar_document(base_doc, sim, seed=seed + i * 2 + 1)

        doc_id_1 = f"doc_{i * 2:04d}"
        doc_id_2 = f"doc_{i * 2 + 1:04d}"

        pairs.append((doc_id_1, base_doc, doc_id_2, similar_doc, sim))

    return pairs


def generate_corpus(
    num_documents: int,
    doc_length: int = 50,
    num_similar_pairs: int = 10,
    similarity_range: Tuple[float, float] = (0.5, 0.9),
    seed: int = 42
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str, float]]]:
    """
    Generate a corpus with some similar document pairs.

    Args:
        num_documents: Total number of documents
        doc_length: Words per document
        num_similar_pairs: Number of intentionally similar pairs
        similarity_range: (min, max) similarity for similar pairs
        seed: Random seed

    Returns:
        Tuple of:
        - List of (doc_id, text) tuples
        - List of (doc_id_1, doc_id_2, expected_similarity) for similar pairs
    """
    random.seed(seed)

    documents = []
    similar_pairs = []

    # Generate base documents
    for i in range(num_documents):
        doc_id = f"doc_{i:04d}"
        text = generate_random_document(doc_length, seed=seed + i)
        documents.append((doc_id, text))

    # Create some intentionally similar pairs
    if num_similar_pairs > 0 and num_documents >= 2:
        available_indices = list(range(num_documents))
        pairs_created = 0

        while pairs_created < num_similar_pairs and len(available_indices) >= 2:
            idx = available_indices.pop(random.randrange(len(available_indices)))
            doc_id, base_text = documents[idx]

            # Create similar version
            sim = random.uniform(*similarity_range)
            similar_text = generate_similar_document(base_text, sim, seed=seed + num_documents + pairs_created)

            # Replace existing document with similar version
            if available_indices:
                replace_idx = available_indices.pop(random.randrange(len(available_indices)))
                other_doc_id = documents[replace_idx][0]
                documents[replace_idx] = (other_doc_id, similar_text)
                similar_pairs.append((doc_id, other_doc_id, sim))
                pairs_created += 1

    return documents, similar_pairs


def create_sample_rdd(
    sc: SparkContext,
    num_documents: int = 20,
    doc_length: int = 50,
    num_similar_pairs: int = 5,
    seed: int = 42
) -> Tuple[RDD, List[Tuple[str, str, float]]]:
    """
    Create a sample RDD for testing.

    Args:
        sc: SparkContext
        num_documents: Number of documents
        doc_length: Words per document
        num_similar_pairs: Number of similar pairs to embed
        seed: Random seed

    Returns:
        Tuple of (docs_rdd, expected_similar_pairs)
    """
    documents, similar_pairs = generate_corpus(
        num_documents=num_documents,
        doc_length=doc_length,
        num_similar_pairs=num_similar_pairs,
        seed=seed
    )

    docs_rdd = sc.parallelize(documents)
    return docs_rdd, similar_pairs


# Pre-generated tiny sample for smoke tests
TINY_SAMPLE = [
    ("doc_001", "the quick brown fox jumps over the lazy dog near the river"),
    ("doc_002", "the quick brown fox leaps over the lazy dog near the stream"),  # Similar to doc_001
    ("doc_003", "data analysis and machine learning algorithms for big data"),
    ("doc_004", "data analysis and deep learning methods for big data"),  # Similar to doc_003
    ("doc_005", "the sun rises in the east and sets in the west every day"),
]


def get_tiny_sample(sc: SparkContext) -> RDD:
    """Get tiny sample dataset for smoke tests."""
    return sc.parallelize(TINY_SAMPLE)
