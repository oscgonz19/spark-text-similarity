# Case Study: Scalable Document Similarity with LSH

## Building a Near-Duplicate Detection System Using Apache Spark

---

## 1. Problem Statement

### The Challenge

A content platform needs to identify similar or duplicate documents across a corpus of millions of documents. Use cases include:

- **Plagiarism detection** in academic submissions
- **Near-duplicate removal** in web crawling
- **Content recommendation** based on similarity
- **News article clustering** for aggregation

### The Scale Problem

For N documents, finding all similar pairs requires comparing every document with every other:

```
Comparisons = N × (N-1) / 2 = O(N²)
```

| Documents | Comparisons | At 1M comparisons/sec |
|-----------|-------------|----------------------|
| 1,000 | 499,500 | 0.5 seconds |
| 10,000 | 49,995,000 | 50 seconds |
| 100,000 | 4,999,950,000 | 83 minutes |
| 1,000,000 | 499,999,500,000 | 5.8 days |

**At 1 million documents, brute force takes nearly 6 days of continuous computation.**

### The Goal

Build a system that:
1. Finds documents with Jaccard similarity ≥ 0.5
2. Scales to millions of documents
3. Maintains high precision and recall
4. Runs on distributed infrastructure (Spark)

---

## 2. Solution Architecture

### Approach: Locality-Sensitive Hashing (LSH)

Instead of comparing all pairs, we use a probabilistic technique that:
1. Hashes similar documents to the same "buckets"
2. Only compares documents within the same bucket
3. Reduces complexity from O(N²) to approximately O(N)

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LSH SIMILARITY PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │          │   │          │   │          │   │          │   │          │ │
│  │   Raw    │──▶│ Shingling│──▶│ MinHash  │──▶│   LSH    │──▶│  Verify  │ │
│  │Documents │   │          │   │          │   │ Banding  │   │          │ │
│  │          │   │          │   │          │   │          │   │          │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│       │              │              │              │              │        │
│       ▼              ▼              ▼              ▼              ▼        │
│    N docs      Sets of k-      Compact       Candidate      Verified      │
│               shingles per   signatures     pairs from     similar        │
│                 document     (100 ints)      buckets        pairs         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Processing | Apache Spark 3.5 | Distributed computation |
| Language | Python 3.11 | Implementation |
| Data Format | RDD | Flexible transformations |
| Testing | pytest | 55 unit tests |
| CI/CD | GitHub Actions | Automated testing |

---

## 3. Implementation

### Stage 1: Shingling

Convert each document into a set of overlapping k-character sequences:

```python
def text_to_shingles(text: str, k: int = 3) -> Set[str]:
    """Convert text to set of k-shingles."""
    text = text.lower().strip()
    return {text[i:i+k] for i in range(len(text) - k + 1)}

# Example:
# "hello" → {"hel", "ell", "llo"}
```

**Why shingling works**: Two similar documents will share many shingles, while different documents will have mostly disjoint shingle sets.

### Stage 2: MinHash Signatures

For each document, compute a compact "signature" of n hash values:

```python
def minhash_signature(shingle_ids: Set[int], hash_params: List[Tuple]) -> List[int]:
    """Compute MinHash signature for a document."""
    signature = []
    for a, b in hash_params:
        min_hash = min((a * s + b) % PRIME for s in shingle_ids)
        signature.append(min_hash)
    return signature
```

**Key property**: The probability that two signatures match at any position equals their Jaccard similarity.

### Stage 3: LSH Banding

Divide signatures into bands and hash each band to buckets:

```python
def lsh_candidates(signatures_rdd: RDD, num_bands: int) -> RDD:
    """Find candidate pairs using LSH."""
    # Hash each band to a bucket
    band_buckets = signatures_rdd.flatMap(
        lambda x: [(band_hash(x[1], i), x[0]) for i in range(num_bands)]
    )
    # Group by bucket, generate pairs
    return band_buckets.groupByKey().flatMap(generate_pairs).distinct()
```

**Documents become candidates if ANY band matches exactly.**

### Stage 4: Verification

Compute exact Jaccard similarity only for candidate pairs:

```python
def jaccard_similarity(set_a: Set, set_b: Set) -> float:
    """Exact Jaccard similarity."""
    return len(set_a & set_b) / len(set_a | set_b)
```

---

## 4. Experimental Results

### Test Configuration

| Parameter | Value |
|-----------|-------|
| Documents | 100 |
| Words per document | 80 |
| Similar pairs embedded | 25 |
| Signature length | 100 |
| Similarity threshold | 0.5 |

### Results by Band Configuration

| Bands (b) | Rows (r) | Threshold | Precision | Recall | F1 | Candidates |
|-----------|----------|-----------|-----------|--------|-----|------------|
| 5 | 20 | 0.923 | - | 0.00 | 0.000 | 0 |
| 10 | 10 | 0.794 | 1.000 | 0.19 | 0.323 | 12 |
| **20** | **5** | **0.549** | **1.000** | **0.85** | **0.917** | **775** |
| 25 | 4 | 0.447 | 1.000 | 1.00 | 1.000 | 2,187 |
| 50 | 2 | 0.141 | 1.000 | 1.00 | 1.000 | 4,947 |

### Key Findings

1. **Optimal configuration**: b=20, r=5 achieves F1=0.917
2. **84% reduction** in comparisons (775 vs 4,950 pairs)
3. **Perfect precision** maintained through verification step
4. **Recall of 85%** catches most similar pairs

### Comparison vs Brute Force

| Metric | Brute Force | LSH (b=20) | Improvement |
|--------|-------------|------------|-------------|
| Comparisons | 4,950 | 775 | 84% fewer |
| Similar pairs found | 26/26 | 22/26 | 85% recall |
| False positives | 0 | 0 | Same |
| Runtime | Baseline | ~Same | - |

---

## 5. Scalability Analysis

### Projected Performance

| Corpus Size | All Pairs | LSH Candidates | Reduction |
|-------------|-----------|----------------|-----------|
| 100 | 4,950 | 775 | 84% |
| 1,000 | 499,500 | ~78K | 84% |
| 10,000 | 50M | ~7.8M | 84% |
| 100,000 | 5B | ~780M | 84% |
| 1,000,000 | 500B | ~78B | 84% |

### Spark Scalability

The pipeline leverages Spark's distributed computing:

- **Shingling**: Embarrassingly parallel (map operation)
- **MinHash**: Parallel with broadcast hash functions
- **LSH**: GroupByKey with controlled bucket sizes
- **Verification**: Parallel with broadcast document lookup

```
                    ┌─────────────────────────────┐
                    │      Spark Driver           │
                    │   (Orchestrates pipeline)   │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
       ┌──────────┐         ┌──────────┐         ┌──────────┐
       │ Worker 1 │         │ Worker 2 │         │ Worker N │
       │ Partition│         │ Partition│         │ Partition│
       │  1..k    │         │ k+1..2k  │         │ ...      │
       └──────────┘         └──────────┘         └──────────┘
```

---

## 6. Trade-offs and Design Decisions

### Precision vs Recall

| Priority | Configuration | Trade-off |
|----------|---------------|-----------|
| High Precision | Fewer bands (b=10) | May miss some similar pairs |
| Balanced | b=20, r=5 | Good precision and recall |
| High Recall | More bands (b=50) | More candidates to verify |

### Memory vs Accuracy

| Choice | Impact |
|--------|--------|
| Longer signatures (n=200) | Better accuracy, 2x memory |
| Shorter signatures (n=50) | Less memory, lower accuracy |
| Optimal (n=100) | Good balance |

### Character vs Word Shingles

| Type | Pros | Cons |
|------|------|------|
| Character (k=3) | Catches typos, robust | Larger vocabulary |
| Word (k=2) | Semantic similarity | Misses typos |

**Decision**: Character-level shingles (k=3) for robustness.

---

## 7. Production Considerations

### Handling Data Skew

If some shingles are very common, buckets become unbalanced:

```python
# Solution: Filter extremely common shingles
vocab_counts = shingles_rdd.flatMap(lambda x: x[1]).countByValue()
rare_shingles = {s for s, c in vocab_counts.items() if c < threshold}
```

### Incremental Updates

For adding new documents without reprocessing:

1. Compute signature for new document
2. Hash to buckets
3. Only compare with documents in same buckets
4. O(1) per new document (amortized)

### Monitoring

Key metrics to track:
- Bucket size distribution (detect skew)
- Candidate pair count (detect parameter drift)
- Verification throughput (bottleneck detection)

---

## 8. Conclusions

### What We Built

A scalable document similarity system that:
- Reduces O(N²) to approximately O(N) comparisons
- Achieves 91.7% F1 score on benchmark
- Maintains 100% precision through verification
- Scales horizontally with Spark

### Key Learnings

1. **LSH is probabilistic but controllable** - tuning b and r gives precise control over precision/recall
2. **Verification is essential** - LSH finds candidates, exact computation confirms
3. **The math works** - theoretical threshold closely matches empirical results

### Future Improvements

1. **Distributed MinHash** using Spark's MLlib
2. **Approximate verification** using signature similarity
3. **Multi-probe LSH** for better recall with fewer bands
4. **Integration with vector databases** (e.g., Milvus, Pinecone)

---

## Appendix: Running the Code

```bash
# Clone and setup
git clone https://github.com/yourusername/spark-text-similarity.git
cd spark-text-similarity
conda env create -f environment.yml
conda activate spark-text-similarity

# Run demo
make run-demo

# Run experiments
make run-experiments

# Run tests
make test
```

---

*This case study demonstrates proficiency in: distributed systems (Spark), algorithm design (LSH), probabilistic data structures (MinHash), experimental methodology, and production engineering.*
