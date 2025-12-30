# Caso de Estudio: Similitud de Documentos Escalable con LSH

## Construyendo un Sistema de Detección de Casi-Duplicados con Apache Spark

---

## 1. Planteamiento del Problema

### El Desafío

Una plataforma de contenido necesita identificar documentos similares o duplicados en un corpus de millones de documentos. Casos de uso incluyen:

- **Detección de plagio** en entregas académicas
- **Eliminación de casi-duplicados** en web crawling
- **Recomendación de contenido** basada en similitud
- **Agrupación de artículos de noticias** para agregación

### El Problema de Escala

Para N documentos, encontrar todos los pares similares requiere comparar cada documento con todos los demás:

```
Comparaciones = N × (N-1) / 2 = O(N²)
```

| Documentos | Comparaciones | A 1M comparaciones/seg |
|------------|---------------|------------------------|
| 1,000 | 499,500 | 0.5 segundos |
| 10,000 | 49,995,000 | 50 segundos |
| 100,000 | 4,999,950,000 | 83 minutos |
| 1,000,000 | 499,999,500,000 | 5.8 días |

**Con 1 millón de documentos, fuerza bruta toma casi 6 días de computación continua.**

### El Objetivo

Construir un sistema que:
1. Encuentre documentos con similitud Jaccard ≥ 0.5
2. Escale a millones de documentos
3. Mantenga alta precisión y recall
4. Corra en infraestructura distribuida (Spark)

---

## 2. Arquitectura de la Solución

### Enfoque: Locality-Sensitive Hashing (LSH)

En lugar de comparar todos los pares, usamos una técnica probabilística que:
1. Hashea documentos similares a los mismos "buckets"
2. Solo compara documentos dentro del mismo bucket
3. Reduce complejidad de O(N²) a aproximadamente O(N)

### Vista General del Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PIPELINE DE SIMILITUD LSH                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │          │   │          │   │          │   │          │   │          │ │
│  │Documentos│──▶│Shingling │──▶│ MinHash  │──▶│   LSH    │──▶│Verificar │ │
│  │  Crudos  │   │          │   │          │   │ Banding  │   │          │ │
│  │          │   │          │   │          │   │          │   │          │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│       │              │              │              │              │        │
│       ▼              ▼              ▼              ▼              ▼        │
│    N docs      Conjuntos de     Firmas        Pares          Pares        │
│               k-shingles por   compactas    candidatos     similares      │
│                 documento     (100 ints)   de buckets    verificados      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| Procesamiento | Apache Spark 3.5 | Computación distribuida |
| Lenguaje | Python 3.11 | Implementación |
| Formato de Datos | RDD | Transformaciones flexibles |
| Testing | pytest | 55 pruebas unitarias |
| CI/CD | GitHub Actions | Testing automatizado |

---

## 3. Implementación

### Etapa 1: Shingling

Convertir cada documento en un conjunto de secuencias superpuestas de k caracteres:

```python
def text_to_shingles(text: str, k: int = 3) -> Set[str]:
    """Convierte texto a conjunto de k-shingles."""
    text = text.lower().strip()
    return {text[i:i+k] for i in range(len(text) - k + 1)}

# Ejemplo:
# "hello" → {"hel", "ell", "llo"}
```

**Por qué funciona el shingling**: Dos documentos similares compartirán muchos shingles, mientras que documentos diferentes tendrán conjuntos de shingles mayormente disjuntos.

### Etapa 2: Firmas MinHash

Para cada documento, calcular una "firma" compacta de n valores hash:

```python
def minhash_signature(shingle_ids: Set[int], hash_params: List[Tuple]) -> List[int]:
    """Calcular firma MinHash para un documento."""
    signature = []
    for a, b in hash_params:
        min_hash = min((a * s + b) % PRIME for s in shingle_ids)
        signature.append(min_hash)
    return signature
```

**Propiedad clave**: La probabilidad de que dos firmas coincidan en cualquier posición es igual a su similitud Jaccard.

### Etapa 3: Banding LSH

Dividir firmas en bandas y hashear cada banda a buckets:

```python
def lsh_candidates(signatures_rdd: RDD, num_bands: int) -> RDD:
    """Encontrar pares candidatos usando LSH."""
    # Hashear cada banda a un bucket
    band_buckets = signatures_rdd.flatMap(
        lambda x: [(band_hash(x[1], i), x[0]) for i in range(num_bands)]
    )
    # Agrupar por bucket, generar pares
    return band_buckets.groupByKey().flatMap(generate_pairs).distinct()
```

**Los documentos se vuelven candidatos si CUALQUIER banda coincide exactamente.**

### Etapa 4: Verificación

Calcular similitud Jaccard exacta solo para pares candidatos:

```python
def jaccard_similarity(set_a: Set, set_b: Set) -> float:
    """Similitud Jaccard exacta."""
    return len(set_a & set_b) / len(set_a | set_b)
```

---

## 4. Resultados Experimentales

### Configuración de Prueba

| Parámetro | Valor |
|-----------|-------|
| Documentos | 100 |
| Palabras por documento | 80 |
| Pares similares insertados | 25 |
| Longitud de firma | 100 |
| Umbral de similitud | 0.5 |

### Resultados por Configuración de Bandas

| Bandas (b) | Filas (r) | Umbral | Precisión | Recall | F1 | Candidatos |
|------------|-----------|--------|-----------|--------|-----|------------|
| 5 | 20 | 0.923 | - | 0.00 | 0.000 | 0 |
| 10 | 10 | 0.794 | 1.000 | 0.19 | 0.323 | 12 |
| **20** | **5** | **0.549** | **1.000** | **0.85** | **0.917** | **775** |
| 25 | 4 | 0.447 | 1.000 | 1.00 | 1.000 | 2,187 |
| 50 | 2 | 0.141 | 1.000 | 1.00 | 1.000 | 4,947 |

### Hallazgos Clave

1. **Configuración óptima**: b=20, r=5 logra F1=0.917
2. **84% de reducción** en comparaciones (775 vs 4,950 pares)
3. **Precisión perfecta** mantenida mediante paso de verificación
4. **Recall de 85%** captura la mayoría de los pares similares

### Comparación vs Fuerza Bruta

| Métrica | Fuerza Bruta | LSH (b=20) | Mejora |
|---------|--------------|------------|--------|
| Comparaciones | 4,950 | 775 | 84% menos |
| Pares similares encontrados | 26/26 | 22/26 | 85% recall |
| Falsos positivos | 0 | 0 | Igual |
| Tiempo de ejecución | Línea base | ~Igual | - |

---

## 5. Análisis de Escalabilidad

### Rendimiento Proyectado

| Tamaño del Corpus | Todos los Pares | Candidatos LSH | Reducción |
|-------------------|-----------------|----------------|-----------|
| 100 | 4,950 | 775 | 84% |
| 1,000 | 499,500 | ~78K | 84% |
| 10,000 | 50M | ~7.8M | 84% |
| 100,000 | 5B | ~780M | 84% |
| 1,000,000 | 500B | ~78B | 84% |

### Escalabilidad en Spark

El pipeline aprovecha la computación distribuida de Spark:

- **Shingling**: Embarazosamente paralelo (operación map)
- **MinHash**: Paralelo con broadcast de funciones hash
- **LSH**: GroupByKey con tamaños de bucket controlados
- **Verificación**: Paralelo con broadcast de lookup de documentos

```
                    ┌─────────────────────────────┐
                    │      Spark Driver           │
                    │   (Orquesta el pipeline)    │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
       ┌──────────┐         ┌──────────┐         ┌──────────┐
       │ Worker 1 │         │ Worker 2 │         │ Worker N │
       │Partición │         │Partición │         │Partición │
       │  1..k    │         │ k+1..2k  │         │ ...      │
       └──────────┘         └──────────┘         └──────────┘
```

---

## 6. Trade-offs y Decisiones de Diseño

### Precisión vs Recall

| Prioridad | Configuración | Trade-off |
|-----------|---------------|-----------|
| Alta Precisión | Menos bandas (b=10) | Puede perder algunos pares similares |
| Balanceado | b=20, r=5 | Buena precisión y recall |
| Alto Recall | Más bandas (b=50) | Más candidatos a verificar |

### Memoria vs Precisión

| Elección | Impacto |
|----------|---------|
| Firmas largas (n=200) | Mejor precisión, 2x memoria |
| Firmas cortas (n=50) | Menos memoria, menor precisión |
| Óptimo (n=100) | Buen balance |

### Shingles de Caracter vs Palabra

| Tipo | Pros | Contras |
|------|------|---------|
| Caracter (k=3) | Captura errores tipográficos, robusto | Vocabulario más grande |
| Palabra (k=2) | Similitud semántica | No detecta errores tipográficos |

**Decisión**: Shingles a nivel de caracter (k=3) por robustez.

---

## 7. Consideraciones de Producción

### Manejo de Data Skew

Si algunos shingles son muy comunes, los buckets se desbalancean:

```python
# Solución: Filtrar shingles extremadamente comunes
vocab_counts = shingles_rdd.flatMap(lambda x: x[1]).countByValue()
rare_shingles = {s for s, c in vocab_counts.items() if c < threshold}
```

### Actualizaciones Incrementales

Para agregar nuevos documentos sin reprocesar:

1. Calcular firma para nuevo documento
2. Hashear a buckets
3. Solo comparar con documentos en los mismos buckets
4. O(1) por nuevo documento (amortizado)

### Monitoreo

Métricas clave a rastrear:
- Distribución de tamaño de buckets (detectar skew)
- Conteo de pares candidatos (detectar drift de parámetros)
- Throughput de verificación (detección de cuellos de botella)

---

## 8. Conclusiones

### Lo que Construimos

Un sistema de similitud de documentos escalable que:
- Reduce O(N²) a aproximadamente O(N) comparaciones
- Logra 91.7% de puntaje F1 en benchmark
- Mantiene 100% de precisión mediante verificación
- Escala horizontalmente con Spark

### Aprendizajes Clave

1. **LSH es probabilístico pero controlable** - ajustar b y r da control preciso sobre precisión/recall
2. **La verificación es esencial** - LSH encuentra candidatos, el cálculo exacto confirma
3. **La matemática funciona** - el umbral teórico coincide cercanamente con resultados empíricos

### Mejoras Futuras

1. **MinHash distribuido** usando MLlib de Spark
2. **Verificación aproximada** usando similitud de firmas
3. **Multi-probe LSH** para mejor recall con menos bandas
4. **Integración con bases de datos vectoriales** (ej. Milvus, Pinecone)

---

## Apéndice: Ejecutar el Código

```bash
# Clonar y configurar
git clone https://github.com/yourusername/spark-text-similarity.git
cd spark-text-similarity
conda env create -f environment.yml
conda activate spark-text-similarity

# Ejecutar demo
make run-demo

# Ejecutar experimentos
make run-experiments

# Ejecutar pruebas
make test
```

---

*Este caso de estudio demuestra competencia en: sistemas distribuidos (Spark), diseño de algoritmos (LSH), estructuras de datos probabilísticas (MinHash), metodología experimental e ingeniería de producción.*
