# spark-text-similarity

[![CI](https://github.com/yourusername/spark-text-similarity/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/spark-text-similarity/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Scalable near-duplicate detection using Shingling + MinHash + LSH with Apache Spark.**

Find similar documents in large corpora efficiently. Instead of comparing all O(n²) document pairs, LSH reduces comparisons to only likely candidates while maintaining high accuracy.

---

## Case Study: Document Similarity at Scale

### The Problem

Given a corpus of **N documents**, find all pairs with **Jaccard similarity ≥ threshold**.

| Approach | Comparisons | N=1,000 | N=100,000 | N=1,000,000 |
|----------|-------------|---------|-----------|-------------|
| **Naive (all pairs)** | O(n²) | 500K | 5 billion | 500 billion |
| **LSH** | O(n) + candidates | ~1K | ~100K | ~1M |

For a million documents, brute force is infeasible. LSH makes it tractable.

### The Solution: LSH Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Documents │───▶│Shingling │───▶│ MinHash  │───▶│   LSH    │───▶│ Verify   │
│          │    │(k-grams) │    │(signatures)│   │(banding) │    │(Jaccard) │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     N docs      Sets of         Compact         Candidate        Exact
                 shingles        signatures      pairs            similarity
```

### Real Experiment Results

**Configuration:**
- 100 synthetic documents, 80 words each
- 25 intentionally similar pairs (similarity 0.5-0.9)
- Signature length: 100 hash functions
- Target threshold: 0.5

**Results by LSH Configuration:**

| Bands (b) | Rows (r) | Threshold τ | Precision | Recall | F1 | Candidates |
|-----------|----------|-------------|-----------|--------|-----|------------|
| 1 | 100 | 1.000 | - | 0.00 | 0.000 | 0 |
| 5 | 20 | 0.923 | - | 0.00 | 0.000 | 0 |
| 10 | 10 | 0.794 | **1.000** | 0.19 | 0.323 | 12 |
| **20** | **5** | **0.549** | **1.000** | **0.85** | **0.917** | 775 |
| 25 | 4 | 0.447 | 1.000 | 1.00 | 1.000 | 2,187 |
| 50 | 2 | 0.141 | 1.000 | 1.00 | 1.000 | 4,947 |

**Key Insights:**

1. **Sweet spot at b=20, r=5**: Threshold ≈ 0.55 matches our target of 0.5
   - F1 = 0.917 with only 775 candidates (vs 4,950 possible pairs)
   - **84% reduction** in comparisons while catching 85% of similar pairs

2. **Perfect recall at b=25**: All similar pairs found, but 2,187 candidates to verify

3. **Precision stays at 100%**: No false positives after Jaccard verification

### The Tradeoff Visualized

```
                    Recall
                      ▲
                 1.0 ─┤                    ●────●────●  (b=25,50,100)
                      │                 ●
                 0.8 ─┤              (b=20)
                      │
                 0.6 ─┤
                      │
                 0.4 ─┤
                      │
                 0.2 ─┤        ●  (b=10)
                      │
                 0.0 ─┼────●────●────●────┬────┬────┬──▶ Bands
                      0    5   10   15   20   25   50

More bands = Lower threshold = Higher recall = More candidates
Fewer bands = Higher threshold = Lower recall = Fewer candidates
```

---

## Quick Start

### Prerequisites

- Python 3.9+
- Java 11 or 17 (for Spark)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/spark-text-similarity.git
cd spark-text-similarity

# Option 1: Using conda (recommended)
conda env create -f environment.yml
conda activate spark-text-similarity

# Option 2: Using pip
pip install -e ".[dev]"
```

### Run Demo

```bash
# Quick demo with 5 sample documents
make run-demo

# Output:
# Loaded 5 documents
# Candidate pairs: 2
# Similar pairs (>= 0.5): 1
# doc_001 <-> doc_002: 0.6667
```

### Run Experiments

```bash
# Run band/row tradeoff analysis
make run-experiments

# Results saved to reports/results.md
```

---

## How It Works

### Step 1: Shingling

Convert documents to sets of overlapping k-character sequences:

```python
"hello world" → {"hel", "ell", "llo", "lo ", "o w", " wo", "wor", "orl", "rld"}
```

Two documents with similar text will share many shingles.

### Step 2: MinHash Signatures

For each document, compute a compact signature of `n` hash values:

```python
# For each of n hash functions:
signature[i] = min(hash_i(shingle) for shingle in document)
```

**Key property**: The probability that two signatures match at position `i` equals their Jaccard similarity:

```
P(sig_A[i] == sig_B[i]) = |A ∩ B| / |A ∪ B| = Jaccard(A, B)
```

### Step 3: LSH Banding

Divide each signature into `b` bands of `r` rows. Hash each band to buckets.

```
Signature (n=12):  [h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12]
                   |____Band 1____| |____Band 2____| |____Band 3____|
                          ↓               ↓                ↓
                       bucket           bucket           bucket
```

**Documents become candidates if ANY band hashes to the same bucket.**

The S-curve probability:
```
P(candidate) = 1 - (1 - s^r)^b

where s = true Jaccard similarity
      r = rows per band
      b = number of bands
```

### Step 4: Verification

Compute exact Jaccard only for candidate pairs. Filter by threshold.

---

## Usage

### As a Library

```python
from pyspark.sql import SparkSession
from src.pipeline import run_lsh_pipeline, LSHConfig

spark = SparkSession.builder.master("local[*]").getOrCreate()
sc = spark.sparkContext

# Your documents as (id, text) tuples
docs_rdd = sc.parallelize([
    ("doc1", "the quick brown fox jumps over the lazy dog"),
    ("doc2", "the quick brown fox leaps over the lazy dog"),
    ("doc3", "pack my box with five dozen liquor jugs"),
])

# Configure and run
config = LSHConfig(
    shingle_size=3,       # 3-character shingles
    num_hashes=100,       # signature length
    num_bands=20,         # 20 bands × 5 rows
    similarity_threshold=0.5
)

result = run_lsh_pipeline(docs_rdd, config)

# Get results
for (doc1, doc2), similarity in result.verified_pairs.collect():
    print(f"{doc1} <-> {doc2}: {similarity:.2%}")
```

### From Command Line

```bash
# With input file (format: id<TAB>text per line)
python scripts/run_pipeline.py --input documents.txt --threshold 0.5

# With custom LSH parameters
python scripts/run_pipeline.py --demo --bands 25 --hashes 100
```

---

## Project Structure

```
spark-text-similarity/
├── src/
│   ├── shingling.py      # Document → k-shingle sets
│   ├── minhash.py        # Shingles → MinHash signatures
│   ├── lsh.py            # Signatures → Candidate pairs
│   ├── jaccard.py        # Exact Jaccard (baseline/verify)
│   ├── pipeline.py       # End-to-end orchestration
│   ├── data_generator.py # Synthetic data (CC0 license)
│   └── experiments.py    # Tradeoff analysis
├── scripts/
│   ├── run_pipeline.py   # CLI for similarity search
│   └── run_experiments.py # CLI for experiments
├── tests/                # 55 tests, 100% pass rate
├── reports/
│   └── results.md        # Experiment results
├── environment.yml       # Conda environment
├── Makefile             # Build automation
└── pyproject.toml       # Project config
```

---

## Choosing Parameters

### For your similarity threshold τ:

| Target τ | Recommended b | r (if n=100) | Expected behavior |
|----------|---------------|--------------|-------------------|
| 0.8+ | 5-10 | 20-10 | High precision, some misses |
| 0.5 | 20 | 5 | Balanced precision/recall |
| 0.3 | 50 | 2 | High recall, more candidates |

### Formula for threshold:

```
τ ≈ (1/b)^(1/r)
```

### Signature length `n`:

- Longer signatures = better accuracy, more memory
- `n = 100` is a good default
- Must be divisible by `b`

---

## Performance

| Corpus Size | Shingling | MinHash | LSH | Total |
|-------------|-----------|---------|-----|-------|
| 100 docs | 0.5s | 0.3s | 0.5s | ~1.5s |
| 1,000 docs | 2s | 1s | 2s | ~5s |
| 10,000 docs | 15s | 8s | 10s | ~35s |

*Tested on local[*] with 8 cores*

**Bottlenecks:**
- Shingling: I/O bound (reading documents)
- MinHash: CPU bound (hashing)
- LSH: Memory bound (bucket grouping)
- Verification: Scales with # candidates

---

## Development

```bash
# Run all tests (55 tests)
make test

# Run smoke tests only (fast, for CI)
make test-smoke

# Run with coverage
make test-cov

# Lint and format
make lint
make format
```

---

## Documentation

Complete documentation is available in **English** and **Español**.

### Quick Links

| Document | EN | ES | Audience |
|----------|----|----|----------|
| **Case Study** | [EN](docs/en/CASE_STUDY.md) | [ES](docs/es/CASE_STUDY.md) | General |
| **Executive Summary** | [EN](docs/en/EXECUTIVE_SUMMARY.md) | [ES](docs/es/EXECUTIVE_SUMMARY.md) | Recruiters / Managers |
| **Technical Appendix** | [EN](docs/en/TECHNICAL_APPENDIX.md) | [ES](docs/es/TECHNICAL_APPENDIX.md) | Tech Leads / Engineers |
| **Pipeline Explained** | [EN](docs/en/PIPELINE_EXPLAINED.md) | [ES](docs/es/PIPELINE_EXPLAINED.md) | Data Scientists / ML Engineers |
| **Mathematical Formulas** | [EN](docs/en/MATHEMATICAL_FORMULAS.md) | [ES](docs/es/MATHEMATICAL_FORMULAS.md) | Statisticians / Quants |

### Documentation Index

- [docs/en/](docs/en/) - All documentation in English
- [docs/es/](docs/es/) - Toda la documentación en Español

### Documentation Structure

```
docs/
├── README.md           # Documentation index (bilingual)
├── en/                 # English documentation
│   ├── CASE_STUDY.md
│   ├── EXECUTIVE_SUMMARY.md
│   ├── TECHNICAL_APPENDIX.md
│   ├── PIPELINE_EXPLAINED.md
│   └── MATHEMATICAL_FORMULAS.md
└── es/                 # Documentación en español
    ├── CASE_STUDY.md
    ├── EXECUTIVE_SUMMARY.md
    ├── TECHNICAL_APPENDIX.md
    ├── PIPELINE_EXPLAINED.md
    └── MATHEMATICAL_FORMULAS.md
```

---

## References

1. Leskovec, Rajaraman, Ullman. [Mining of Massive Datasets](http://www.mmds.org/), Chapter 3
2. Broder, A. (1997). On the resemblance and containment of documents. *SEQUENCES '97*
3. Indyk, P., & Motwani, R. (1998). Approximate nearest neighbors: towards removing the curse of dimensionality. *STOC '98*

---

## License

MIT License - see [LICENSE](LICENSE) for details.

**Note**: All sample data is synthetically generated and released under CC0 (public domain).
