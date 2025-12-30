# Pipeline Explicado

## Cómo Funciona el Pipeline de Detección de Similitud

---

## Visión General

Este documento proporciona un recorrido detallado del pipeline de similitud LSH, explicando cada etapa con visualizaciones y ejemplos.

---

## El Pipeline Completo

```
ENTRADA                  ETAPA 1           ETAPA 2           ETAPA 3           ETAPA 4           SALIDA
───────                  ───────           ───────           ───────           ───────           ──────

┌─────────────┐     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│             │     │             │   │             │   │             │   │             │   │             │
│   Corpus    │────▶│  SHINGLING  │──▶│   MINHASH   │──▶│     LSH     │──▶│  VERIFICAR  │──▶│   Pares     │
│     de      │     │             │   │             │   │   BANDING   │   │             │   │  Similares  │
│ Documentos  │     │             │   │             │   │             │   │             │   │             │
└─────────────┘     └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
                           │                 │                 │                 │
                           ▼                 ▼                 ▼                 ▼
                      "hola" →          {14, 892,       ¿Hash de banda   Cálculo exacto
                      {hol,ola}         23, 567,        coincide? →      de Jaccard
                                        ...}            ¡Candidato!
```

---

## Etapa 1: Shingling

### Qué Hace

Convierte cada documento en un **conjunto de secuencias superpuestas de k caracteres** (shingles).

### Por Qué Funciona

- Documentos similares comparten muchos shingles
- Documentos diferentes tienen conjuntos de shingles mayormente disjuntos
- El orden no importa (representación como conjunto)

### Ejemplo

```
Documento: "el gato se"
k = 3 (nivel de caracter)

Extracción paso a paso:
Posición 0: "el "
Posición 1: "l g"
Posición 2: " ga"
Posición 3: "gat"
Posición 4: "ato"
Posición 5: "to "
Posición 6: "o s"
Posición 7: " se"

Resultado: {"el ", "l g", " ga", "gat", "ato", "to ", "o s", " se"}
```

### Representación Visual

```
Documento A: "el gato negro corre"
Documento B: "el gato negro salta"

Shingles A: {el , l g,  ga, gat, ato, to , o n,  ne, neg, egr, gro, ro , o c,  co, cor, orr, rre}
Shingles B: {el , l g,  ga, gat, ato, to , o n,  ne, neg, egr, gro, ro , o s,  sa, sal, alt, lta}
             ▲   ▲    ▲   ▲   ▲   ▲   ▲    ▲   ▲   ▲   ▲   ▲
             └───┴────┴───┴───┴───┴───┴────┴───┴───┴───┴───┘
                         SHINGLES COMPARTIDOS (alto traslape = similar)
```

### Selección del Tamaño de Shingle

| k | Pros | Contras | Caso de Uso |
|---|------|---------|-------------|
| 2 | Más coincidencias | Demasiadas colisiones | Textos muy cortos |
| **3** | **Buen balance** | **Elección estándar** | **Texto general** |
| 4 | Menos colisiones | Puede perder similitudes | Documentos grandes |
| 5+ | Muy específico | Necesita texto casi idéntico | Detección de plagio |

---

## Etapa 2: Firmas MinHash

### Qué Hace

Comprime el conjunto de shingles de cada documento en una **firma de longitud fija** de n enteros.

### La Idea Clave

Para una función hash aleatoria h y dos conjuntos A y B:

```
P(min(h(A)) = min(h(B))) = |A ∩ B| / |A ∪ B| = Jaccard(A, B)
```

¡La probabilidad de que dos conjuntos tengan el mismo hash mínimo es igual a su similitud Jaccard!

### Cómo Funciona

```
Para cada una de las n funciones hash:
    firma[i] = min(hash_i(shingle) para todos los shingles del documento)
```

### Ejemplo

```
Shingles del documento: {"gat", "ato", "to "}
IDs de shingles: {14, 892, 456}  (del vocabulario)

Función hash 1: h(x) = (3x + 7) mod 1000
    h(14)  = 49
    h(892) = 683
    h(456) = 375
    firma[0] = min(49, 683, 375) = 49

Función hash 2: h(x) = (5x + 11) mod 1000
    h(14)  = 81
    h(892) = 471
    h(456) = 291
    firma[1] = min(81, 471, 291) = 81

... repetir para todas las n funciones hash ...

Firma final: [49, 81, 234, 567, ...]  (n enteros)
```

### Visual: Comparación de Firmas

```
Firma Documento A: [49,  81, 234, 567, 123, 890, 45,  678, 901, 234]
Firma Documento B: [49,  81, 234, 111, 123, 555, 45,  678, 333, 234]
                    ═══  ═══ ═══       ═══       ═══  ═══       ═══
                    7 coincidencias de 10 → Similitud estimada ≈ 0.70

Similitud Jaccard real: 0.68 (¡coincidencia cercana!)
```

### ¿Por qué n=100?

| n | Precisión | Memoria | Notas |
|---|-----------|---------|-------|
| 25 | ±20% | 100 bytes | Muy ruidoso |
| 50 | ±14% | 200 bytes | Aceptable |
| **100** | **±10%** | **400 bytes** | **Buen balance** |
| 200 | ±7% | 800 bytes | Rendimientos decrecientes |

Error estándar ≈ 1/√n

---

## Etapa 3: Banding LSH

### Qué Hace

Divide las firmas en **b bandas de r filas** cada una, hasheando cada banda a buckets para encontrar pares candidatos.

### La Idea Central

- Si dos documentos son similares, al menos una banda probablemente coincidirá
- Si dos documentos son diferentes, todas las bandas probablemente diferirán

### Cómo Funciona

```
Firma (n=12):  [h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12]

Con b=4 bandas, r=3 filas:

Banda 1: [h1, h2, h3]   → hash → bucket_1a
Banda 2: [h4, h5, h6]   → hash → bucket_2b
Banda 3: [h7, h8, h9]   → hash → bucket_3c
Banda 4: [h10,h11,h12]  → hash → bucket_4d

Los documentos se vuelven CANDIDATOS si CUALQUIER banda hashea al mismo bucket.
```

### Visual: Proceso de Banding

```
Documento A: [14, 23, 67, 89, 12, 45, 78, 90, 34, 56, 11, 22]
Documento B: [14, 23, 67, 55, 12, 99, 78, 90, 34, 56, 11, 22]
             ════════════  ══════════  ══════════════════════
               Banda 1       Banda 2        Banda 3+4

Banda 1: [14,23,67] vs [14,23,67] → MISMO HASH → ¡CANDIDATOS!
Banda 2: [89,12,45] vs [55,12,99] → Hash diferente
Banda 3: [78,90,34] vs [78,90,34] → Mismo hash (bonus)
Banda 4: [56,11,22] vs [56,11,22] → Mismo hash (bonus)

Resultado: A y B son PARES CANDIDATOS (serán verificados)
```

### La Curva S

La probabilidad de volverse candidatos sigue una curva en forma de S:

```
P(candidato) = 1 - (1 - s^r)^b

donde: s = similitud Jaccard real
       r = filas por banda
       b = número de bandas
```

```
        Probabilidad de volverse candidatos
        1.0 ┤                          ●●●●●●
            │                       ●●●
            │                     ●●
        0.8 ┤                   ●●
            │                  ●
            │                 ●
        0.6 ┤                ●
            │               ●         ← Umbral τ ≈ 0.55
        0.5 ┼ ─ ─ ─ ─ ─ ─ ─●─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
            │              ●
        0.4 ┤             ●
            │            ●
            │           ●
        0.2 ┤         ●●
            │       ●●
            │    ●●●
        0.0 ┼●●●●─────┬─────┬─────┬─────┬─────┬──▶ Similitud real
            0.0  0.2  0.4  0.6  0.8  1.0

                     Configuración: b=20, r=5
```

### Elegir b y r

| Objetivo | Bandas (b) | Filas (r) | Umbral | Efecto |
|----------|------------|-----------|--------|--------|
| Estricto | 5 | 20 | 0.92 | Solo pares muy similares |
| Moderado | 10 | 10 | 0.79 | Balanceado |
| **Recomendado** | **20** | **5** | **0.55** | **Bueno para τ=0.5** |
| Permisivo | 50 | 2 | 0.14 | Captura similitudes débiles |

---

## Etapa 4: Verificación

### Qué Hace

Calcula la **similitud Jaccard exacta** para pares candidatos y filtra por umbral.

### Por Qué Verificar

LSH genera candidatos (puede incluir falsos positivos). La verificación asegura precisión.

```
Salida LSH (Candidatos):
├── (doc1, doc2) → Verificar → Jaccard = 0.72 ✓ MANTENER
├── (doc1, doc5) → Verificar → Jaccard = 0.65 ✓ MANTENER
├── (doc3, doc7) → Verificar → Jaccard = 0.31 ✗ DESCARTAR (bajo 0.5)
└── (doc4, doc9) → Verificar → Jaccard = 0.58 ✓ MANTENER

Salida Final: [(doc1,doc2,0.72), (doc1,doc5,0.65), (doc4,doc9,0.58)]
```

### Cálculo de Jaccard

```python
def jaccard_similarity(set_a: Set, set_b: Set) -> float:
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0
```

### Ejemplo

```
Shingles Doc A: {gat, ato, mat, som, bra}
Shingles Doc B: {gat, ato, rat, pat, mat}

Intersección: {gat, ato, mat} → 3 elementos
Unión: {gat, ato, mat, som, bra, rat, pat} → 7 elementos

Jaccard = 3/7 = 0.4286

Si umbral = 0.5: DESCARTAR (0.43 < 0.5)
Si umbral = 0.4: MANTENER (0.43 ≥ 0.4)
```

---

## Ejemplo End-to-End

### Entrada

```
doc_001: "el rápido zorro marrón salta sobre el perro perezoso"
doc_002: "el rápido zorro marrón brinca sobre el perro perezoso"
doc_003: "empaca mi caja con cinco docenas de jarras de licor"
```

### Etapa 1: Shingling (k=3)

```
doc_001 → {"el ", "l r", " rá", "ráp", "ápi", "pid", "ido", ...} (48 shingles)
doc_002 → {"el ", "l r", " rá", "ráp", "ápi", "pid", "ido", ...} (49 shingles)
doc_003 → {"emp", "mpa", "pac", "aca", "ca ", "a m", " mi", ...} (47 shingles)

Observación: doc_001 y doc_002 comparten ~90% de shingles
             doc_003 no comparte casi nada con los otros
```

### Etapa 2: MinHash (n=100)

```
doc_001 → [234, 567, 89, 123, 456, 789, 12, 345, 678, 901, ...]
doc_002 → [234, 567, 89, 123, 456, 789, 12, 999, 678, 901, ...]
doc_003 → [111, 222, 333, 444, 555, 666, 777, 888, 999, 000, ...]

Similitud de firmas (001 vs 002): 92/100 = 0.92
Similitud de firmas (001 vs 003): 3/100 = 0.03
```

### Etapa 3: LSH Banding (b=20, r=5)

```
doc_001, Banda 3: [89, 123, 456, 789, 12] → hash = 847291
doc_002, Banda 3: [89, 123, 456, 789, 12] → hash = 847291  ← ¡COINCIDE!

Resultado: (doc_001, doc_002) es un PAR CANDIDATO
           (doc_001, doc_003) NO es candidato (ninguna banda coincide)
           (doc_002, doc_003) NO es candidato
```

### Etapa 4: Verificación

```
Candidatos: [(doc_001, doc_002)]

Verificar (doc_001, doc_002):
  - Recuperar conjuntos de shingles
  - Calcular Jaccard exacto = 0.9024
  - Umbral = 0.5
  - 0.9024 ≥ 0.5 → MANTENER

Salida Final: [(doc_001, doc_002, 0.9024)]
```

---

## Implementación en Spark

### Flujo de Datos

```
docs_rdd: RDD[(doc_id, text)]
    │
    ▼ flatMap: text_to_shingles
shingles_rdd: RDD[(doc_id, Set[str])]
    │
    ▼ map: build_vocabulary, shingles_to_ids
shingle_ids_rdd: RDD[(doc_id, Set[int])]
    │
    ▼ map: minhash_signature (con broadcast hash_params)
signatures_rdd: RDD[(doc_id, List[int])]
    │
    ▼ flatMap: emit_band_buckets
band_buckets_rdd: RDD[(band_bucket_hash, doc_id)]
    │
    ▼ groupByKey, flatMap: generate_pairs
candidates_rdd: RDD[(doc_id_1, doc_id_2)]
    │
    ▼ map: compute_jaccard (con broadcast shingles)
verified_rdd: RDD[((doc_id_1, doc_id_2), similarity)]
    │
    ▼ filter: similarity >= threshold
output_rdd: RDD[((doc_id_1, doc_id_2), similarity)]
```

### Optimizaciones Clave

1. **Variables Broadcast**: Evitar shuffle de parámetros hash y tablas de lookup de shingles
2. **Distinct**: Eliminar pares candidatos duplicados
3. **Evaluación Lazy**: Encadenar operaciones sin materializar intermedios

---

## Resumen

| Etapa | Entrada | Salida | Complejidad |
|-------|---------|--------|-------------|
| Shingling | Texto | Conjunto de k-shingles | O(len(texto)) |
| MinHash | Conjunto de shingles | Firma (n enteros) | O(n × |shingles|) |
| LSH Banding | Firma | Asignaciones a bucket | O(b) |
| Generación de Candidatos | Buckets | Pares candidatos | O(tamaño_bucket²) |
| Verificación | Pares candidatos | Pares verificados | O(|candidatos| × |shingles|) |

**En general**: O(N) + O(candidatos × verificación) en lugar de O(N²)

---

*Para demostraciones matemáticas, ver [Fórmulas Matemáticas](./MATHEMATICAL_FORMULAS.md).*

**English**: [View documentation in English](../en/)
