# LSH Experiment Results

## Executive Summary

This report analyzes the precision/recall tradeoffs of Locality-Sensitive Hashing (LSH) for document similarity detection. We find that **b=20 bands with r=5 rows** provides the optimal balance for a similarity threshold of 0.5, achieving **F1=0.917** while reducing candidate comparisons by **84%**.

---

## Experimental Setup

### Corpus Generation

| Parameter | Value |
|-----------|-------|
| Documents | 100 |
| Words per document | 80 |
| Vocabulary | 120 common English words |
| Similar pairs embedded | 25 |
| Similarity range | 0.5 - 0.9 |
| Random seed | 42 (reproducible) |

### LSH Configuration

| Parameter | Value |
|-----------|-------|
| Shingle size (k) | 3 characters |
| Shingle type | Character-level |
| Signature length (n) | 100 hash functions |
| Similarity threshold | 0.5 |

### Ground Truth

After computing exact Jaccard similarity for all 4,950 document pairs:
- **26 pairs** have similarity ≥ 0.5
- These are the "true positives" we aim to find

---

## Results

### Band Configuration Sweep

| Bands | Rows | Threshold | Precision | Recall | F1 | Candidates | Runtime |
|-------|------|-----------|-----------|--------|-----|------------|---------|
| 1 | 100 | 1.000 | - | 0.000 | 0.000 | 0 | 2.78s |
| 2 | 50 | 0.986 | - | 0.000 | 0.000 | 0 | 1.85s |
| 4 | 25 | 0.946 | - | 0.000 | 0.000 | 0 | 1.58s |
| 5 | 20 | 0.923 | - | 0.000 | 0.000 | 0 | 1.47s |
| 10 | 10 | 0.794 | 1.000 | 0.192 | 0.323 | 12 | 1.37s |
| **20** | **5** | **0.549** | **1.000** | **0.846** | **0.917** | **775** | **1.34s** |
| 25 | 4 | 0.447 | 1.000 | 1.000 | 1.000 | 2,187 | 1.42s |
| 50 | 2 | 0.141 | 1.000 | 1.000 | 1.000 | 4,947 | 1.27s |
| 100 | 1 | 0.010 | 1.000 | 1.000 | 1.000 | 4,950 | 1.35s |

### Metrics Explanation

- **Threshold**: Theoretical similarity where P(candidate) = 0.5, calculated as `(1/b)^(1/r)`
- **Precision**: TP / (TP + FP) — all detected pairs are truly similar (after verification)
- **Recall**: TP / (TP + FN) — fraction of true similar pairs detected
- **Candidates**: Number of pairs flagged by LSH (before Jaccard verification)

---

## Analysis

### 1. The S-Curve Effect

LSH exhibits a characteristic S-curve behavior:

```
P(candidate | similarity=s) = 1 - (1 - s^r)^b
```

For our configurations:

| Config | s=0.3 | s=0.5 | s=0.7 | s=0.9 |
|--------|-------|-------|-------|-------|
| b=10, r=10 | 0.00 | 0.00 | 0.03 | 0.65 |
| b=20, r=5 | 0.00 | 0.47 | 0.94 | 1.00 |
| b=50, r=2 | 0.32 | 0.97 | 1.00 | 1.00 |

At **b=20, r=5**, documents with similarity 0.5 have ~47% chance of becoming candidates, while those with similarity 0.7+ have >94% chance.

### 2. Threshold Alignment

The theoretical threshold for b=20, r=5 is:
```
τ = (1/20)^(1/5) = 0.549
```

This closely matches our target of 0.5, explaining the strong performance.

### 3. Candidate Reduction

| Config | Candidates | vs All Pairs | Recall |
|--------|------------|--------------|--------|
| b=10, r=10 | 12 | 0.24% | 19.2% |
| b=20, r=5 | 775 | 15.7% | 84.6% |
| b=25, r=4 | 2,187 | 44.2% | 100% |
| b=50, r=2 | 4,947 | 99.9% | 100% |

**Key insight**: At b=20, we examine only 15.7% of pairs but find 84.6% of similar documents.

### 4. Precision Remains Perfect

All configurations show **100% precision** because:
1. LSH generates candidates (may include false positives)
2. We verify each candidate with exact Jaccard
3. Only pairs above threshold are reported

The "false positives" from LSH are filtered out during verification.

---

## Recommendations

### For Similarity Threshold ≈ 0.5

**Use b=20, r=5** (F1 = 0.917)
- Best balance of precision and recall
- 84% reduction in comparisons
- Misses only 15% of similar pairs

### For Perfect Recall (find ALL similar pairs)

**Use b=25, r=4** (F1 = 1.000)
- Finds all 26 similar pairs
- Examines 44% of all pairs
- Still 56% reduction vs brute force

### For Minimal Computation

**Use b=10, r=10** (F1 = 0.323)
- Only 12 candidates to verify
- Finds only high-similarity pairs (>0.8)
- Use when missing some pairs is acceptable

---

## Scalability Projection

Based on our results, projecting to larger corpora:

| Corpus Size | All Pairs | LSH Candidates (b=20) | Reduction |
|-------------|-----------|----------------------|-----------|
| 100 | 4,950 | ~775 | 84% |
| 1,000 | 499,500 | ~78,000 | 84% |
| 10,000 | 49,995,000 | ~7,800,000 | 84% |
| 100,000 | 4.99 billion | ~780 million | 84% |

At 100K documents, LSH reduces comparisons from 5 billion to 780 million.

---

## Reproducing These Results

```bash
# Activate environment
conda activate spark-text-similarity

# Run experiments
python scripts/run_experiments.py \
    --num-docs 100 \
    --doc-length 80 \
    --num-similar 25 \
    --threshold 0.5 \
    --seed 42 \
    --output-dir reports
```

---

## Raw Data

Full results available in: `reports/experiment_results.csv`

---

*Generated with spark-text-similarity v0.1.0*
