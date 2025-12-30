"""
Pytest configuration and fixtures for Spark tests.
"""

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    """Create a SparkSession for testing."""
    spark = SparkSession.builder \
        .appName("LSH-Tests") \
        .master("local[2]") \
        .config("spark.driver.memory", "1g") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    yield spark

    spark.stop()


@pytest.fixture(scope="session")
def sc(spark):
    """Get SparkContext from SparkSession."""
    return spark.sparkContext


@pytest.fixture
def sample_docs(sc):
    """Sample documents for testing."""
    docs = [
        ("doc1", "the quick brown fox jumps over the lazy dog"),
        ("doc2", "the quick brown fox leaps over the lazy dog"),  # Similar to doc1
        ("doc3", "pack my box with five dozen liquor jugs"),
        ("doc4", "how vexingly quick daft zebras jump"),
        ("doc5", "the five boxing wizards jump quickly"),
    ]
    return sc.parallelize(docs)


@pytest.fixture
def identical_docs(sc):
    """Identical documents for edge case testing."""
    docs = [
        ("doc1", "exactly the same text here"),
        ("doc2", "exactly the same text here"),
    ]
    return sc.parallelize(docs)


@pytest.fixture
def empty_docs(sc):
    """Empty documents for edge case testing."""
    docs = [
        ("doc1", ""),
        ("doc2", "   "),
        ("doc3", "some actual content here"),
    ]
    return sc.parallelize(docs)
