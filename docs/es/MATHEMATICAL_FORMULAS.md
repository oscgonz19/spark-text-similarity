# Fórmulas Matemáticas

## Derivaciones para MinHash, LSH y Cálculos de Probabilidad

---

## Tabla de Contenidos

1. [Similitud de Jaccard](#1-similitud-de-jaccard)
2. [Teoría de MinHash](#2-teoría-de-minhash)
3. [Análisis de Probabilidad LSH](#3-análisis-de-probabilidad-lsh)
4. [Derivación del Umbral](#4-derivación-del-umbral)
5. [Análisis de Error](#5-análisis-de-error)
6. [Optimización de Parámetros](#6-optimización-de-parámetros)

---

## 1. Similitud de Jaccard

### Definición

Para dos conjuntos A y B, la **similitud de Jaccard** (o índice de Jaccard) se define como:

$$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

### Propiedades

1. **Acotada**: $0 \leq J(A, B) \leq 1$
2. **Simétrica**: $J(A, B) = J(B, A)$
3. **Identidad**: $J(A, A) = 1$
4. **Conjuntos disjuntos**: Si $A \cap B = \emptyset$, entonces $J(A, B) = 0$

### Distancia de Jaccard

La **distancia de Jaccard** es una métrica:

$$d_J(A, B) = 1 - J(A, B) = \frac{|A \cup B| - |A \cap B|}{|A \cup B|}$$

Esta satisface la desigualdad triangular:

$$d_J(A, C) \leq d_J(A, B) + d_J(B, C)$$

---

## 2. Teoría de MinHash

### Teorema Fundamental

**Teorema (Propiedad MinHash)**: Sea $h$ una función hash aleatoria de una familia de permutaciones min-wise independientes. Para conjuntos A y B:

$$P[\min_{a \in A} h(a) = \min_{b \in B} h(b)] = J(A, B)$$

### Demostración

Consideremos la unión $U = A \cup B$. Para cualquier elemento $x \in U$, definimos:

$$\mathbb{1}_A(x) = \begin{cases} 1 & \text{si } x \in A \\ 0 & \text{en otro caso} \end{cases}$$

Para una permutación aleatoria $\pi$ de $U$, sea $x^* = \arg\min_{x \in U} \pi(x)$ el elemento con el menor valor hash.

Entonces:
$$P[\min(h(A)) = \min(h(B))] = P[x^* \in A \cap B]$$

Como $\pi$ es una permutación aleatoria, cada elemento de $U$ tiene igual probabilidad de ser el mínimo:

$$P[x^* \in A \cap B] = \frac{|A \cap B|}{|A \cup B|} = J(A, B) \quad \blacksquare$$

### Estimación por Firma

Para una firma de longitud $n$, el estimador:

$$\hat{J}(A, B) = \frac{1}{n} \sum_{i=1}^{n} \mathbb{1}[\text{sig}_A[i] = \text{sig}_B[i]]$$

es un **estimador insesgado** de $J(A, B)$:

$$E[\hat{J}(A, B)] = J(A, B)$$

---

## 3. Análisis de Probabilidad LSH

### Técnica de Banding

Dados:
- Longitud de firma: $n$
- Número de bandas: $b$
- Filas por banda: $r$ (donde $n = b \times r$)

### Probabilidad de Coincidencia de Banda

Para dos documentos con similitud Jaccard real $s$, la probabilidad de que una sola banda de $r$ filas coincida exactamente:

$$P[\text{banda coincide}] = s^r$$

Esto se cumple porque cada fila coincide independientemente con probabilidad $s$.

### Probabilidad de Volverse Candidatos

Los documentos se vuelven candidatos si **al menos una banda coincide**. La probabilidad de que ninguna banda coincida es:

$$P[\text{ninguna banda coincide}] = (1 - s^r)^b$$

Por lo tanto, la probabilidad de volverse candidatos:

$$P[\text{candidato} | s] = 1 - (1 - s^r)^b$$

### La Curva S

Esta función exhibe una curva en forma de S con:

1. **Transición pronunciada** alrededor del umbral
2. **Baja probabilidad** para pares disímiles ($s$ pequeña)
3. **Alta probabilidad** para pares similares ($s$ grande)

```
P(candidato)
    │
1.0 ┤                    ╭──────────
    │                   ╱
    │                  ╱
    │                 ╱
0.5 ┼────────────────╳────────────── (umbral τ)
    │               ╱
    │              ╱
    │            ╱
0.0 ┼───────────╯
    └────┬────┬────┬────┬────┬────▶ s
        0.2  0.4  τ   0.8  1.0
```

---

## 4. Derivación del Umbral

### Definición

El **umbral** $\tau$ es el valor de similitud donde:

$$P[\text{candidato} | s = \tau] = 0.5$$

### Derivación

Igualando la probabilidad de candidato a 0.5:

$$1 - (1 - \tau^r)^b = 0.5$$

$$(1 - \tau^r)^b = 0.5$$

$$1 - \tau^r = 0.5^{1/b}$$

$$\tau^r = 1 - 0.5^{1/b}$$

$$\tau = (1 - 0.5^{1/b})^{1/r}$$

### Aproximación

Para $b$ grande, usando $(1 - x) \approx e^{-x}$ para $x$ pequeña:

$$\tau \approx \left(\frac{1}{b}\right)^{1/r}$$

### Ejemplos

| b | r | τ Exacta | τ Aprox |
|---|---|----------|---------|
| 5 | 20 | 0.9227 | 0.9233 |
| 10 | 10 | 0.7943 | 0.7943 |
| 20 | 5 | 0.5493 | 0.5493 |
| 25 | 4 | 0.4467 | 0.4472 |
| 50 | 2 | 0.1409 | 0.1414 |

---

## 5. Análisis de Error

### Varianza del Estimador MinHash

Para el estimador basado en firma con $n$ funciones hash:

$$\text{Var}[\hat{J}] = \frac{J(1-J)}{n}$$

### Error Estándar

$$\text{SE}[\hat{J}] = \sqrt{\frac{J(1-J)}{n}} \leq \frac{1}{2\sqrt{n}}$$

El máximo ocurre en $J = 0.5$.

| n | SE Máx | Ancho IC 95% |
|---|--------|--------------|
| 25 | 0.10 | ±0.20 |
| 50 | 0.071 | ±0.14 |
| 100 | 0.050 | ±0.10 |
| 200 | 0.035 | ±0.07 |

### Tasas de Falsos Positivos y Falsos Negativos

**Tasa de Falsos Positivos** (pares disímiles que se vuelven candidatos):

$$\text{TFP}(s) = 1 - (1 - s^r)^b \quad \text{para } s < \tau$$

**Tasa de Falsos Negativos** (pares similares que no se vuelven candidatos):

$$\text{TFN}(s) = (1 - s^r)^b \quad \text{para } s \geq \tau$$

### Error Esperado en el Umbral

En $s = \tau$:
- TFP = TFN = 0.5

Este es el peor escenario, donde el algoritmo es esencialmente aleatorio.

---

## 6. Optimización de Parámetros

### Función Objetivo

Para minimizar el error esperado mientras se controla el conteo de candidatos:

$$\min_{b,r} \quad \alpha \cdot \text{TFN}(\tau_{objetivo}) + (1-\alpha) \cdot E[\text{candidatos}]$$

donde $\alpha$ pondera la importancia del recall vs. el cómputo.

### Configuración Óptima

Para un umbral objetivo $\tau_{objetivo}$:

1. Elegir $r$ tal que:
   $$r \approx \frac{\log(1/b)}{\log(\tau_{objetivo})}$$

2. Esto da umbral aproximado:
   $$\tau \approx \tau_{objetivo}$$

### Análisis de Trade-off

| Prioridad | Estrategia | Resultado |
|-----------|------------|-----------|
| Alto Recall | Disminuir $r$, aumentar $b$ | Más candidatos, menos omisiones |
| Pocos Falsos Positivos | Aumentar $r$, disminuir $b$ | Menos candidatos, más omisiones |
| Balanceado | $\tau \approx \tau_{objetivo}$ | Puntaje F1 óptimo |

### Número Esperado de Candidatos

Para $N$ documentos con distribución de similitud $f(s)$:

$$E[\text{candidatos}] = \binom{N}{2} \int_0^1 [1 - (1 - s^r)^b] f(s) \, ds$$

Para similitudes uniformemente distribuidas:

$$E[\text{candidatos}] \approx \binom{N}{2} \cdot \tau$$

---

## Resumen de Fórmulas Clave

### Similitud de Jaccard
$$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

### Propiedad MinHash
$$P[\min(h(A)) = \min(h(B))] = J(A, B)$$

### Probabilidad de Candidato LSH
$$P[\text{candidato} | s] = 1 - (1 - s^r)^b$$

### Umbral
$$\tau = (1 - 0.5^{1/b})^{1/r} \approx \left(\frac{1}{b}\right)^{1/r}$$

### Varianza de Estimación por Firma
$$\text{Var}[\hat{J}] = \frac{J(1-J)}{n}$$

---

## Referencias

1. Broder, A. Z. (1997). On the resemblance and containment of documents. *Proceedings of Compression and Complexity of Sequences*, 21-29.

2. Indyk, P., & Motwani, R. (1998). Approximate nearest neighbors: towards removing the curse of dimensionality. *STOC '98*, 604-613.

3. Leskovec, J., Rajaraman, A., & Ullman, J. D. (2014). *Mining of Massive Datasets*. Cambridge University Press. Capítulo 3.

4. Gionis, A., Indyk, P., & Motwani, R. (1999). Similarity search in high dimensions via hashing. *VLDB '99*, 518-529.

---

*Este documento proporciona la fundamentación matemática para la implementación de spark-text-similarity.*
