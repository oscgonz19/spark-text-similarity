# Technical Appendix

## Detailed Implementation Documentation

---

## Table of Contents

1. [Module Architecture](#1-module-architecture)
2. [API Reference](#2-api-reference)
3. [Configuration Options](#3-configuration-options)
4. [Performance Tuning](#4-performance-tuning)
5. [Testing Strategy](#5-testing-strategy)
6. [Deployment Guide](#6-deployment-guide)

---

## 1. Module Architecture

### Project Structure

```
spark-text-similarity/
├── src/
│   ├── __init__.py
│   ├── shingling.py      # Document tokenization
│   ├── minhash.py        # Signature generation
│   ├── lsh.py            # Locality-sensitive hashing
│   ├── jaccard.py        # Exact similarity computation
│   ├── pipeline.py       # End-to-end orchestration
│   ├── data_generator.py # Synthetic data generation
│   └── experiments.py    # Experiment runner
├── scripts/
│   ├── run_pipeline.py   # CLI for similarity search
│   └── run_experiments.py # CLI for experiments
├── tests/
│   ├── conftest.py       # pytest fixtures
│   ├── test_shingling.py
│   ├── test_minhash.py
│   ├── test_lsh.py
│   ├── test_jaccard.py
│   └── test_pipeline.py
└── docs/
```

### Module Dependencies

```
┌──────────────────────────────────────────────────────────────────┐
│                         pipeline.py                              │
│                    (Orchestration Layer)                         │
└───────────┬───────────┬───────────┬───────────┬─────────────────┘
            │           │           │           │
            ▼           ▼           ▼           ▼
     ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
     │shingling │ │ minhash  │ │   lsh    │ │ jaccard  │
     │   .py    │ │   .py    │ │   .py    │ │   .py    │
     └──────────┘ └──────────┘ └──────────┘ └──────────┘
            │           │           │           │
            └───────────┴─────┬─────┴───────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    PySpark      │
                    │ (SparkContext,  │
                    │     RDD)        │
                    └─────────────────┘
```

---

## 2. API Reference

### shingling.py

#### `text_to_shingles(text, k=3, char_level=True)`

Convert text to a set of k-shingles.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | required | Input document text |
| `k` | `int` | `3` | Shingle size |
| `char_level` | `bool` | `True` | Character-level (True) or word-level (False) |

**Returns:** `Set[str]` - Set of k-shingles

**Example:**
```python
from src.shingling import text_to_shingles

shingles = text_to_shingles("hello world", k=3)
# Returns: {'hel', 'ell', 'llo', 'lo ', 'o w', ' wo', 'wor', 'orl', 'rld'}
```

#### `shingles_to_ids(shingles, vocab)`

Convert shingle strings to integer IDs.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `shingles` | `Set[str]` | Set of shingle strings |
| `vocab` | `Dict[str, int]` | Vocabulary mapping |

**Returns:** `Set[int]` - Set of shingle IDs

---

### minhash.py

#### `generate_hash_params(num_hashes, seed=42)`

Generate random hash function parameters.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_hashes` | `int` | required | Number of hash functions |
| `seed` | `int` | `42` | Random seed for reproducibility |

**Returns:** `List[Tuple[int, int]]` - List of (a, b) parameters

#### `minhash_signature(shingle_ids, hash_params, num_buckets=LARGE_PRIME)`

Compute MinHash signature for a document.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `shingle_ids` | `Set[int]` | required | Set of shingle IDs |
| `hash_params` | `List[Tuple]` | required | Hash function parameters |
| `num_buckets` | `int` | `LARGE_PRIME` | Hash bucket count |

**Returns:** `List[int]` - MinHash signature

**Example:**
```python
from src.minhash import generate_hash_params, minhash_signature

params = generate_hash_params(100)
sig = minhash_signature({1, 5, 10, 15}, params)
# Returns: [23451, 8923, 45123, ...] (100 integers)
```

#### `estimate_similarity(sig_a, sig_b)`

Estimate Jaccard similarity from signatures.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `sig_a` | `List[int]` | First signature |
| `sig_b` | `List[int]` | Second signature |

**Returns:** `float` - Estimated similarity [0, 1]

---

### lsh.py

#### `lsh_candidates(signatures_rdd, num_bands)`

Find candidate pairs using LSH banding.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `signatures_rdd` | `RDD[(id, signature)]` | Document signatures |
| `num_bands` | `int` | Number of bands |

**Returns:** `RDD[(id1, id2)]` - Candidate pairs

**Example:**
```python
from src.lsh import lsh_candidates

# signatures_rdd: RDD of (doc_id, signature_list)
candidates = lsh_candidates(signatures_rdd, num_bands=20)
# Returns: RDD of (doc_id_1, doc_id_2) pairs
```

#### `compute_threshold(num_bands, rows_per_band)`

Compute theoretical similarity threshold.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `num_bands` | `int` | Number of bands |
| `rows_per_band` | `int` | Rows per band |

**Returns:** `float` - Threshold where P(candidate) = 0.5

---

### jaccard.py

#### `jaccard_similarity(set_a, set_b)`

Compute exact Jaccard similarity.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `set_a` | `Set` | First set |
| `set_b` | `Set` | Second set |

**Returns:** `float` - Jaccard similarity [0, 1]

#### `all_pairs_similarity(docs_rdd)`

Compute similarity for all document pairs (brute force).

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `docs_rdd` | `RDD[(id, Set)]` | Document shingle sets |

**Returns:** `RDD[((id1, id2), float)]` - All pairs with similarity

---

### pipeline.py

#### `LSHConfig` (dataclass)

Configuration for the LSH pipeline.

```python
@dataclass
class LSHConfig:
    shingle_size: int = 3        # k for k-shingles
    char_level: bool = True      # Character vs word shingles
    num_hashes: int = 100        # Signature length
    num_bands: int = 20          # LSH bands (n must be divisible by b)
    similarity_threshold: float = 0.5  # Output threshold
```

#### `LSHResult` (dataclass)

Result from the LSH pipeline.

```python
@dataclass
class LSHResult:
    candidate_pairs: RDD       # Raw candidates from LSH
    verified_pairs: RDD        # Pairs above threshold
    num_candidates: int        # Candidate count
    num_verified: int          # Verified count
    config: LSHConfig          # Configuration used
```

#### `run_lsh_pipeline(docs_rdd, config)`

Execute the complete LSH pipeline.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `docs_rdd` | `RDD[(id, text)]` | Input documents |
| `config` | `LSHConfig` | Pipeline configuration |

**Returns:** `LSHResult` - Pipeline results

---

## 3. Configuration Options

### LSH Parameter Selection

| Target Similarity | Bands (b) | Rows (r) | Notes |
|-------------------|-----------|----------|-------|
| ≥ 0.9 | 5 | 20 | Very strict |
| ≥ 0.7 | 10 | 10 | Strict |
| ≥ 0.5 | 20 | 5 | **Recommended** |
| ≥ 0.3 | 50 | 2 | Permissive |

### Memory Considerations

| Corpus Size | Recommended Signature Length | Memory per Doc |
|-------------|------------------------------|----------------|
| < 10K | 100 | 400 bytes |
| 10K - 100K | 100 | 400 bytes |
| 100K - 1M | 50-100 | 200-400 bytes |
| > 1M | 50 | 200 bytes |

### Spark Configuration

```python
spark = SparkSession.builder \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()
```

---

## 4. Performance Tuning

### Bottleneck Analysis

| Stage | Bottleneck | Mitigation |
|-------|------------|------------|
| Shingling | I/O | Increase partitions |
| MinHash | CPU | More executors |
| LSH Banding | Shuffle | Tune partitions |
| Verification | Memory | Broadcast shingles |

### Optimizations Implemented

1. **Broadcast Variables**: Hash parameters and vocabulary are broadcast to all workers

```python
hash_params_bc = sc.broadcast(hash_params)
vocab_bc = sc.broadcast(vocab)
```

2. **Partition Tuning**: Documents are repartitioned based on corpus size

```python
optimal_partitions = max(200, num_docs // 1000)
docs_rdd = docs_rdd.repartition(optimal_partitions)
```

3. **Lazy Evaluation**: Operations are chained without materializing intermediate results

---

## 5. Testing Strategy

### Test Categories

| Category | Count | Purpose |
|----------|-------|---------|
| Unit tests | 40 | Individual function correctness |
| Integration tests | 10 | Module interactions |
| Property tests | 5 | Mathematical invariants |

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_minhash.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Smoke tests only (fast)
pytest tests/ -v -m smoke
```

### Key Test Cases

```python
# Shingling: empty input
def test_empty_text_returns_empty_set():
    assert text_to_shingles("") == set()

# MinHash: signature length
def test_signature_length_matches_num_hashes():
    params = generate_hash_params(100)
    sig = minhash_signature({1, 2, 3}, params)
    assert len(sig) == 100

# LSH: identical documents are candidates
def test_identical_docs_become_candidates():
    # ... creates identical docs, verifies they're candidates

# Jaccard: similarity bounds
def test_jaccard_between_zero_and_one():
    sim = jaccard_similarity({1, 2}, {2, 3})
    assert 0 <= sim <= 1
```

---

## 6. Deployment Guide

### Local Development

```bash
# Setup
conda env create -f environment.yml
conda activate spark-text-similarity

# Verify
make test-smoke
```

### Production Cluster

```bash
# Submit to Spark cluster
spark-submit \
    --master yarn \
    --deploy-mode cluster \
    --num-executors 10 \
    --executor-memory 8g \
    --executor-cores 4 \
    scripts/run_pipeline.py \
    --input hdfs:///data/documents.txt \
    --output hdfs:///results/similar_pairs
```

### Docker (Optional)

```dockerfile
FROM openjdk:17-slim

RUN pip install pyspark==3.5.0
COPY . /app
WORKDIR /app

CMD ["python", "scripts/run_pipeline.py", "--demo"]
```

### CI/CD Pipeline

The GitHub Actions workflow:

1. **Matrix Testing**: Python 3.9, 3.10, 3.11
2. **Java Setup**: OpenJDK 17
3. **Smoke Tests**: Fast subset for CI
4. **Full Tests**: On main branch only

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    steps:
      - uses: actions/setup-java@v4
        with:
          java-version: '17'
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v -m smoke
```

---

## Appendix: Constants

```python
# src/minhash.py
LARGE_PRIME = 2147483647  # 2^31 - 1 (Mersenne prime)
MAX_HASH = 2**31 - 1

# src/lsh.py
DEFAULT_BANDS = 20
DEFAULT_SIGNATURE_LENGTH = 100
```

---

*For mathematical derivations, see [Mathematical Formulas](./MATHEMATICAL_FORMULAS.md).*

**Español**: [Ver documentación en español](../es/)
