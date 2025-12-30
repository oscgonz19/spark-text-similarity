# Pipeline Explained

## How the Similarity Detection Pipeline Works

---

## Overview

This document provides a detailed walkthrough of the LSH similarity pipeline, explaining each stage with visualizations and examples.

---

## The Complete Pipeline

```
INPUT                    STAGE 1           STAGE 2           STAGE 3           STAGE 4           OUTPUT
─────                    ───────           ───────           ───────           ───────           ──────

┌─────────────┐     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│             │     │             │   │             │   │             │   │             │   │             │
│  Document   │────▶│  SHINGLING  │──▶│   MINHASH   │──▶│     LSH     │──▶│   VERIFY    │──▶│   Similar   │
│   Corpus    │     │             │   │             │   │   BANDING   │   │             │   │    Pairs    │
│             │     │             │   │             │   │             │   │             │   │             │
└─────────────┘     └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
                           │                 │                 │                 │
                           ▼                 ▼                 ▼                 ▼
                      "hello" →         {14, 892,       Band hashes      Exact Jaccard
                      {hel,ell,         23, 567,        match? →         computation
                       llo}             ...}            Candidate!
```

---

## Stage 1: Shingling

### What It Does

Converts each document into a **set of overlapping k-character sequences** (shingles).

### Why It Works

- Similar documents share many shingles
- Different documents have mostly disjoint shingle sets
- Order doesn't matter (set representation)

### Example

```
Document: "the cat sat"
k = 3 (character-level)

Step-by-step extraction:
Position 0: "the"
Position 1: "he "
Position 2: "e c"
Position 3: " ca"
Position 4: "cat"
Position 5: "at "
Position 6: "t s"
Position 7: " sa"
Position 8: "sat"

Result: {"the", "he ", "e c", " ca", "cat", "at ", "t s", " sa", "sat"}
```

### Visual Representation

```
Document A: "the cat sat on the mat"
Document B: "the cat sat by the mat"

Shingles A: {the, he , e c,  ca, cat, at , t s,  sa, sat, at , t o,  on, on , n t,  th, the, he , e m,  ma, mat}
Shingles B: {the, he , e c,  ca, cat, at , t s,  sa, sat, at , t b,  by, by , y t,  th, the, he , e m,  ma, mat}
                ▲   ▲   ▲    ▲   ▲   ▲   ▲    ▲   ▲   ▲                   ▲   ▲   ▲   ▲    ▲   ▲
                └───┴───┴────┴───┴───┴───┴────┴───┴───┴───────────────────┴───┴───┴───┴────┴───┘
                                    SHARED SHINGLES (high overlap = similar)
```

### Shingle Size Selection

| k | Pros | Cons | Use Case |
|---|------|------|----------|
| 2 | More matches | Too many collisions | Very short texts |
| **3** | **Good balance** | **Standard choice** | **General text** |
| 4 | Fewer collisions | May miss similarities | Large documents |
| 5+ | Very specific | Need near-identical text | Plagiarism detection |

---

## Stage 2: MinHash Signatures

### What It Does

Compresses each document's shingle set into a **fixed-length signature** of n integers.

### The Key Insight

For a random hash function h and two sets A and B:

```
P(min(h(A)) = min(h(B))) = |A ∩ B| / |A ∪ B| = Jaccard(A, B)
```

The probability that two sets have the same minimum hash equals their Jaccard similarity!

### How It Works

```
For each of n hash functions:
    signature[i] = min(hash_i(shingle) for all shingles in document)
```

### Example

```
Document shingles: {"cat", "sat", "mat"}
Shingle IDs: {14, 892, 456}  (from vocabulary)

Hash function 1: h(x) = (3x + 7) mod 1000
    h(14)  = 49
    h(892) = 683
    h(456) = 375
    signature[0] = min(49, 683, 375) = 49

Hash function 2: h(x) = (5x + 11) mod 1000
    h(14)  = 81
    h(892) = 471
    h(456) = 291
    signature[1] = min(81, 471, 291) = 81

... repeat for all n hash functions ...

Final signature: [49, 81, 234, 567, ...]  (n integers)
```

### Visual: Signature Comparison

```
Document A signature: [49,  81, 234, 567, 123, 890, 45,  678, 901, 234]
Document B signature: [49,  81, 234, 111, 123, 555, 45,  678, 333, 234]
                       ═══  ═══ ═══       ═══       ═══  ═══       ═══
                       7 matches out of 10 → Estimated similarity ≈ 0.70

True Jaccard similarity: 0.68 (close match!)
```

### Why n=100?

| n | Accuracy | Memory | Notes |
|---|----------|--------|-------|
| 25 | ±20% | 100 bytes | Too noisy |
| 50 | ±14% | 200 bytes | Acceptable |
| **100** | **±10%** | **400 bytes** | **Good balance** |
| 200 | ±7% | 800 bytes | Diminishing returns |

Standard error ≈ 1/√n

---

## Stage 3: LSH Banding

### What It Does

Divides signatures into **b bands of r rows** each, hashing each band to buckets to find candidate pairs.

### The Core Idea

- If two documents are similar, at least one band will likely match
- If two documents are different, all bands will likely differ

### How It Works

```
Signature (n=12):  [h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12]

With b=4 bands, r=3 rows:

Band 1: [h1, h2, h3]   → hash → bucket_1a
Band 2: [h4, h5, h6]   → hash → bucket_2b
Band 3: [h7, h8, h9]   → hash → bucket_3c
Band 4: [h10,h11,h12]  → hash → bucket_4d

Documents become CANDIDATES if ANY band hashes to the same bucket.
```

### Visual: Banding Process

```
Document A: [14, 23, 67, 89, 12, 45, 78, 90, 34, 56, 11, 22]
Document B: [14, 23, 67, 55, 12, 99, 78, 90, 34, 56, 11, 22]
            ════════════  ══════════  ══════════════════════
               Band 1        Band 2        Band 3+4

Band 1: [14,23,67] vs [14,23,67] → SAME HASH → CANDIDATES!
Band 2: [89,12,45] vs [55,12,99] → Different hash
Band 3: [78,90,34] vs [78,90,34] → Same hash (bonus)
Band 4: [56,11,22] vs [56,11,22] → Same hash (bonus)

Result: A and B are CANDIDATE PAIRS (will be verified)
```

### The S-Curve

The probability of becoming candidates follows an S-shaped curve:

```
P(candidate) = 1 - (1 - s^r)^b

where: s = true Jaccard similarity
       r = rows per band
       b = number of bands
```

```
        Probability of becoming candidates
        1.0 ┤                          ●●●●●●
            │                       ●●●
            │                     ●●
        0.8 ┤                   ●●
            │                  ●
            │                 ●
        0.6 ┤                ●
            │               ●         ← Threshold τ ≈ 0.55
        0.5 ┼ ─ ─ ─ ─ ─ ─ ─●─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
            │              ●
        0.4 ┤             ●
            │            ●
            │           ●
        0.2 ┤         ●●
            │       ●●
            │    ●●●
        0.0 ┼●●●●─────┬─────┬─────┬─────┬─────┬──▶ True similarity
            0.0  0.2  0.4  0.6  0.8  1.0

                     Configuration: b=20, r=5
```

### Choosing b and r

| Goal | Bands (b) | Rows (r) | Threshold | Effect |
|------|-----------|----------|-----------|--------|
| Strict | 5 | 20 | 0.92 | Only very similar pairs |
| Moderate | 10 | 10 | 0.79 | Balanced |
| **Recommended** | **20** | **5** | **0.55** | **Good for τ=0.5** |
| Permissive | 50 | 2 | 0.14 | Catches weak similarities |

---

## Stage 4: Verification

### What It Does

Computes **exact Jaccard similarity** for candidate pairs and filters by threshold.

### Why Verification?

LSH generates candidates (may include false positives). Verification ensures accuracy.

```
LSH Output (Candidates):
├── (doc1, doc2) → Verify → Jaccard = 0.72 ✓ KEEP
├── (doc1, doc5) → Verify → Jaccard = 0.65 ✓ KEEP
├── (doc3, doc7) → Verify → Jaccard = 0.31 ✗ DISCARD (below 0.5)
└── (doc4, doc9) → Verify → Jaccard = 0.58 ✓ KEEP

Final Output: [(doc1,doc2,0.72), (doc1,doc5,0.65), (doc4,doc9,0.58)]
```

### Jaccard Computation

```python
def jaccard_similarity(set_a: Set, set_b: Set) -> float:
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0
```

### Example

```
Doc A shingles: {cat, sat, mat, hat, bat}
Doc B shingles: {cat, sat, rat, pat, mat}

Intersection: {cat, sat, mat} → 3 elements
Union: {cat, sat, mat, hat, bat, rat, pat} → 7 elements

Jaccard = 3/7 = 0.4286

If threshold = 0.5: DISCARD (0.43 < 0.5)
If threshold = 0.4: KEEP (0.43 ≥ 0.4)
```

---

## End-to-End Example

### Input

```
doc_001: "the quick brown fox jumps over the lazy dog"
doc_002: "the quick brown fox leaps over the lazy dog"
doc_003: "pack my box with five dozen liquor jugs"
```

### Stage 1: Shingling (k=3)

```
doc_001 → {"the", "he ", "e q", " qu", "qui", "uic", "ick", ...} (41 shingles)
doc_002 → {"the", "he ", "e q", " qu", "qui", "uic", "ick", ...} (41 shingles)
doc_003 → {"pac", "ack", "ck ", "k m", " my", "my ", ...} (39 shingles)

Observation: doc_001 and doc_002 share ~90% of shingles
             doc_003 shares almost nothing with the others
```

### Stage 2: MinHash (n=100)

```
doc_001 → [234, 567, 89, 123, 456, 789, 12, 345, 678, 901, ...]
doc_002 → [234, 567, 89, 123, 456, 789, 12, 999, 678, 901, ...]
doc_003 → [111, 222, 333, 444, 555, 666, 777, 888, 999, 000, ...]

Signature similarity (001 vs 002): 92/100 = 0.92
Signature similarity (001 vs 003): 3/100 = 0.03
```

### Stage 3: LSH Banding (b=20, r=5)

```
doc_001, Band 3: [89, 123, 456, 789, 12] → hash = 847291
doc_002, Band 3: [89, 123, 456, 789, 12] → hash = 847291  ← MATCH!

Result: (doc_001, doc_002) is a CANDIDATE PAIR
        (doc_001, doc_003) NOT a candidate (no band matches)
        (doc_002, doc_003) NOT a candidate
```

### Stage 4: Verification

```
Candidates: [(doc_001, doc_002)]

Verify (doc_001, doc_002):
  - Retrieve shingle sets
  - Compute exact Jaccard = 0.9024
  - Threshold = 0.5
  - 0.9024 ≥ 0.5 → KEEP

Final Output: [(doc_001, doc_002, 0.9024)]
```

---

## Spark Implementation

### Data Flow

```
docs_rdd: RDD[(doc_id, text)]
    │
    ▼ flatMap: text_to_shingles
shingles_rdd: RDD[(doc_id, Set[str])]
    │
    ▼ map: build_vocabulary, shingles_to_ids
shingle_ids_rdd: RDD[(doc_id, Set[int])]
    │
    ▼ map: minhash_signature (with broadcast hash_params)
signatures_rdd: RDD[(doc_id, List[int])]
    │
    ▼ flatMap: emit_band_buckets
band_buckets_rdd: RDD[(band_bucket_hash, doc_id)]
    │
    ▼ groupByKey, flatMap: generate_pairs
candidates_rdd: RDD[(doc_id_1, doc_id_2)]
    │
    ▼ map: compute_jaccard (with broadcast shingles)
verified_rdd: RDD[((doc_id_1, doc_id_2), similarity)]
    │
    ▼ filter: similarity >= threshold
output_rdd: RDD[((doc_id_1, doc_id_2), similarity)]
```

### Key Optimizations

1. **Broadcast Variables**: Avoid shuffling hash parameters and shingle lookup tables
2. **Distinct**: Remove duplicate candidate pairs
3. **Lazy Evaluation**: Chain operations without materializing intermediates

---

## Summary

| Stage | Input | Output | Complexity |
|-------|-------|--------|------------|
| Shingling | Text | Set of k-shingles | O(len(text)) |
| MinHash | Set of shingles | Signature (n ints) | O(n × |shingles|) |
| LSH Banding | Signature | Bucket assignments | O(b) |
| Candidate Generation | Buckets | Candidate pairs | O(bucket_size²) |
| Verification | Candidate pairs | Verified pairs | O(|candidates| × |shingles|) |

**Overall**: O(N) + O(candidates × verification) instead of O(N²)

---

*For mathematical proofs, see [Mathematical Formulas](./MATHEMATICAL_FORMULAS.md).*

**Español**: [Ver documentación en español](../es/)
