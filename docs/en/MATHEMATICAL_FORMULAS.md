# Mathematical Formulas

## Derivations for MinHash, LSH, and Probability Calculations

---

## Table of Contents

1. [Jaccard Similarity](#1-jaccard-similarity)
2. [MinHash Theory](#2-minhash-theory)
3. [LSH Probability Analysis](#3-lsh-probability-analysis)
4. [Threshold Derivation](#4-threshold-derivation)
5. [Error Analysis](#5-error-analysis)
6. [Parameter Optimization](#6-parameter-optimization)

---

## 1. Jaccard Similarity

### Definition

For two sets A and B, the **Jaccard similarity** (or Jaccard index) is defined as:

$$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

### Properties

1. **Bounded**: $0 \leq J(A, B) \leq 1$
2. **Symmetric**: $J(A, B) = J(B, A)$
3. **Identity**: $J(A, A) = 1$
4. **Disjoint sets**: If $A \cap B = \emptyset$, then $J(A, B) = 0$

### Jaccard Distance

The **Jaccard distance** is a metric:

$$d_J(A, B) = 1 - J(A, B) = \frac{|A \cup B| - |A \cap B|}{|A \cup B|}$$

This satisfies the triangle inequality:

$$d_J(A, C) \leq d_J(A, B) + d_J(B, C)$$

---

## 2. MinHash Theory

### Fundamental Theorem

**Theorem (MinHash Property)**: Let $h$ be a random hash function from a family of min-wise independent permutations. For sets A and B:

$$P[\min_{a \in A} h(a) = \min_{b \in B} h(b)] = J(A, B)$$

### Proof

Consider the union $U = A \cup B$. For any element $x \in U$, define:

$$\mathbb{1}_A(x) = \begin{cases} 1 & \text{if } x \in A \\ 0 & \text{otherwise} \end{cases}$$

For a random permutation $\pi$ of $U$, let $x^* = \arg\min_{x \in U} \pi(x)$ be the element with the smallest hash value.

Then:
$$P[\min(h(A)) = \min(h(B))] = P[x^* \in A \cap B]$$

Since $\pi$ is a random permutation, each element of $U$ is equally likely to be the minimum:

$$P[x^* \in A \cap B] = \frac{|A \cap B|}{|A \cup B|} = J(A, B) \quad \blacksquare$$

### Signature Estimation

For a signature of length $n$, the estimator:

$$\hat{J}(A, B) = \frac{1}{n} \sum_{i=1}^{n} \mathbb{1}[\text{sig}_A[i] = \text{sig}_B[i]]$$

is an **unbiased estimator** of $J(A, B)$:

$$E[\hat{J}(A, B)] = J(A, B)$$

---

## 3. LSH Probability Analysis

### Banding Technique

Given:
- Signature length: $n$
- Number of bands: $b$
- Rows per band: $r$ (where $n = b \times r$)

### Probability of Band Match

For two documents with true Jaccard similarity $s$, the probability that a single band of $r$ rows matches exactly:

$$P[\text{band matches}] = s^r$$

This follows because each row matches independently with probability $s$.

### Probability of Becoming Candidates

Documents become candidates if **at least one band matches**. The probability of no bands matching is:

$$P[\text{no band matches}] = (1 - s^r)^b$$

Therefore, the probability of becoming candidates:

$$P[\text{candidate} | s] = 1 - (1 - s^r)^b$$

### The S-Curve

This function exhibits an S-shaped curve with:

1. **Steep transition** around the threshold
2. **Low probability** for dissimilar pairs (small $s$)
3. **High probability** for similar pairs (large $s$)

```
P(candidate)
    │
1.0 ┤                    ╭──────────
    │                   ╱
    │                  ╱
    │                 ╱
0.5 ┼────────────────╳────────────── (threshold τ)
    │               ╱
    │              ╱
    │            ╱
0.0 ┼───────────╯
    └────┬────┬────┬────┬────┬────▶ s
        0.2  0.4  τ   0.8  1.0
```

---

## 4. Threshold Derivation

### Definition

The **threshold** $\tau$ is the similarity value where:

$$P[\text{candidate} | s = \tau] = 0.5$$

### Derivation

Setting the candidate probability to 0.5:

$$1 - (1 - \tau^r)^b = 0.5$$

$$(1 - \tau^r)^b = 0.5$$

$$1 - \tau^r = 0.5^{1/b}$$

$$\tau^r = 1 - 0.5^{1/b}$$

$$\tau = (1 - 0.5^{1/b})^{1/r}$$

### Approximation

For large $b$, using $(1 - x) \approx e^{-x}$ for small $x$:

$$\tau \approx \left(\frac{1}{b}\right)^{1/r}$$

### Examples

| b | r | Exact τ | Approx τ |
|---|---|---------|----------|
| 5 | 20 | 0.9227 | 0.9233 |
| 10 | 10 | 0.7943 | 0.7943 |
| 20 | 5 | 0.5493 | 0.5493 |
| 25 | 4 | 0.4467 | 0.4472 |
| 50 | 2 | 0.1409 | 0.1414 |

---

## 5. Error Analysis

### Variance of MinHash Estimator

For the signature-based estimator with $n$ hash functions:

$$\text{Var}[\hat{J}] = \frac{J(1-J)}{n}$$

### Standard Error

$$\text{SE}[\hat{J}] = \sqrt{\frac{J(1-J)}{n}} \leq \frac{1}{2\sqrt{n}}$$

The maximum occurs at $J = 0.5$.

| n | Max SE | 95% CI Width |
|---|--------|--------------|
| 25 | 0.10 | ±0.20 |
| 50 | 0.071 | ±0.14 |
| 100 | 0.050 | ±0.10 |
| 200 | 0.035 | ±0.07 |

### False Positive and False Negative Rates

**False Positive Rate** (dissimilar pairs becoming candidates):

$$\text{FPR}(s) = 1 - (1 - s^r)^b \quad \text{for } s < \tau$$

**False Negative Rate** (similar pairs not becoming candidates):

$$\text{FNR}(s) = (1 - s^r)^b \quad \text{for } s \geq \tau$$

### Expected Error at Threshold

At $s = \tau$:
- FPR = FNR = 0.5

This is the worst-case scenario, where the algorithm is essentially random.

---

## 6. Parameter Optimization

### Objective Function

To minimize expected error while controlling candidate count:

$$\min_{b,r} \quad \alpha \cdot \text{FNR}(\tau_{target}) + (1-\alpha) \cdot E[\text{candidates}]$$

where $\alpha$ weights the importance of recall vs. computation.

### Optimal Configuration

For a target threshold $\tau_{target}$:

1. Choose $r$ such that:
   $$r \approx \frac{\log(1/b)}{\log(\tau_{target})}$$

2. This gives approximate threshold:
   $$\tau \approx \tau_{target}$$

### Trade-off Analysis

| Priority | Strategy | Result |
|----------|----------|--------|
| High Recall | Decrease $r$, increase $b$ | More candidates, fewer misses |
| Low False Positives | Increase $r$, decrease $b$ | Fewer candidates, more misses |
| Balanced | $\tau \approx \tau_{target}$ | Optimal F1 score |

### Expected Number of Candidates

For $N$ documents with similarity distribution $f(s)$:

$$E[\text{candidates}] = \binom{N}{2} \int_0^1 [1 - (1 - s^r)^b] f(s) \, ds$$

For uniformly distributed similarities:

$$E[\text{candidates}] \approx \binom{N}{2} \cdot \tau$$

---

## Summary of Key Formulas

### Jaccard Similarity
$$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

### MinHash Property
$$P[\min(h(A)) = \min(h(B))] = J(A, B)$$

### LSH Candidate Probability
$$P[\text{candidate} | s] = 1 - (1 - s^r)^b$$

### Threshold
$$\tau = (1 - 0.5^{1/b})^{1/r} \approx \left(\frac{1}{b}\right)^{1/r}$$

### Signature Estimation Variance
$$\text{Var}[\hat{J}] = \frac{J(1-J)}{n}$$

---

## References

1. Broder, A. Z. (1997). On the resemblance and containment of documents. *Proceedings of Compression and Complexity of Sequences*, 21-29.

2. Indyk, P., & Motwani, R. (1998). Approximate nearest neighbors: towards removing the curse of dimensionality. *STOC '98*, 604-613.

3. Leskovec, J., Rajaraman, A., & Ullman, J. D. (2014). *Mining of Massive Datasets*. Cambridge University Press. Chapter 3.

4. Gionis, A., Indyk, P., & Motwani, R. (1999). Similarity search in high dimensions via hashing. *VLDB '99*, 518-529.

---

*This document provides the mathematical foundation for the spark-text-similarity implementation.*
