"""
Shingling module: Convert documents to sets of k-shingles.

A k-shingle is a contiguous subsequence of k tokens (characters or words).
"""

from typing import Set

from pyspark.rdd import RDD


def text_to_shingles(text: str, k: int = 3, char_level: bool = True) -> Set[str]:
    """
    Convert a text document to a set of k-shingles.

    Args:
        text: Input document text
        k: Shingle size (default 3)
        char_level: If True, use character-level shingles;
                   if False, use word-level shingles

    Returns:
        Set of unique k-shingles
    """
    text = text.lower().strip()

    if char_level:
        # Character-level: sliding window of k characters
        if len(text) < k:
            return {text} if text else set()
        return {text[i:i+k] for i in range(len(text) - k + 1)}
    else:
        # Word-level: sliding window of k words
        words = text.split()
        if len(words) < k:
            return {" ".join(words)} if words else set()
        return {" ".join(words[i:i+k]) for i in range(len(words) - k + 1)}


def shingle_document(doc_id: str, text: str, k: int = 3, char_level: bool = True) -> tuple:
    """
    Create shingle set for a document with its ID.

    Args:
        doc_id: Document identifier
        text: Document text
        k: Shingle size
        char_level: Character or word level shingling

    Returns:
        Tuple of (doc_id, shingle_set)
    """
    shingles = text_to_shingles(text, k, char_level)
    return (doc_id, shingles)


def create_shingle_rdd(
    docs_rdd: RDD,
    k: int = 3,
    char_level: bool = True
) -> RDD:
    """
    Transform an RDD of (doc_id, text) to (doc_id, shingle_set).

    Args:
        docs_rdd: RDD of (doc_id, text) tuples
        k: Shingle size
        char_level: Character or word level shingling

    Returns:
        RDD of (doc_id, shingle_set) tuples
    """
    return docs_rdd.map(
        lambda x: shingle_document(x[0], x[1], k, char_level)
    )


def get_shingle_vocabulary(shingles_rdd: RDD) -> dict:
    """
    Create a vocabulary mapping shingles to integer IDs.

    Args:
        shingles_rdd: RDD of (doc_id, shingle_set) tuples

    Returns:
        Dictionary mapping shingle -> integer ID
    """
    all_shingles = (
        shingles_rdd
        .flatMap(lambda x: x[1])
        .distinct()
        .collect()
    )
    return {shingle: idx for idx, shingle in enumerate(sorted(all_shingles))}


def shingles_to_ids(
    shingles_rdd: RDD,
    vocab: dict
) -> RDD:
    """
    Convert shingle sets to sets of integer IDs using vocabulary.

    Args:
        shingles_rdd: RDD of (doc_id, shingle_set) tuples
        vocab: Dictionary mapping shingle -> integer ID

    Returns:
        RDD of (doc_id, set of integer IDs)
    """
    vocab_broadcast = shingles_rdd.context.broadcast(vocab)

    def convert(doc_shingles):
        doc_id, shingles = doc_shingles
        ids = {vocab_broadcast.value[s] for s in shingles if s in vocab_broadcast.value}
        return (doc_id, ids)

    return shingles_rdd.map(convert)
