# Apéndice Técnico

## Documentación Detallada de Implementación

---

## Tabla de Contenidos

1. [Arquitectura de Módulos](#1-arquitectura-de-módulos)
2. [Referencia de API](#2-referencia-de-api)
3. [Opciones de Configuración](#3-opciones-de-configuración)
4. [Optimización de Rendimiento](#4-optimización-de-rendimiento)
5. [Estrategia de Testing](#5-estrategia-de-testing)
6. [Guía de Despliegue](#6-guía-de-despliegue)

---

## 1. Arquitectura de Módulos

### Estructura del Proyecto

```
spark-text-similarity/
├── src/
│   ├── __init__.py
│   ├── shingling.py      # Tokenización de documentos
│   ├── minhash.py        # Generación de firmas
│   ├── lsh.py            # Locality-sensitive hashing
│   ├── jaccard.py        # Cálculo de similitud exacta
│   ├── pipeline.py       # Orquestación end-to-end
│   ├── data_generator.py # Generación de datos sintéticos
│   └── experiments.py    # Ejecutor de experimentos
├── scripts/
│   ├── run_pipeline.py   # CLI para búsqueda de similitud
│   └── run_experiments.py # CLI para experimentos
├── tests/
│   ├── conftest.py       # fixtures de pytest
│   ├── test_shingling.py
│   ├── test_minhash.py
│   ├── test_lsh.py
│   ├── test_jaccard.py
│   └── test_pipeline.py
└── docs/
```

### Dependencias entre Módulos

```
┌──────────────────────────────────────────────────────────────────┐
│                         pipeline.py                              │
│                    (Capa de Orquestación)                        │
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

## 2. Referencia de API

### shingling.py

#### `text_to_shingles(text, k=3, char_level=True)`

Convierte texto a un conjunto de k-shingles.

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `text` | `str` | requerido | Texto del documento de entrada |
| `k` | `int` | `3` | Tamaño del shingle |
| `char_level` | `bool` | `True` | Nivel de caracter (True) o palabra (False) |

**Retorna:** `Set[str]` - Conjunto de k-shingles

**Ejemplo:**
```python
from src.shingling import text_to_shingles

shingles = text_to_shingles("hello world", k=3)
# Retorna: {'hel', 'ell', 'llo', 'lo ', 'o w', ' wo', 'wor', 'orl', 'rld'}
```

#### `shingles_to_ids(shingles, vocab)`

Convierte strings de shingles a IDs enteros.

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `shingles` | `Set[str]` | Conjunto de strings de shingles |
| `vocab` | `Dict[str, int]` | Mapeo de vocabulario |

**Retorna:** `Set[int]` - Conjunto de IDs de shingles

---

### minhash.py

#### `generate_hash_params(num_hashes, seed=42)`

Genera parámetros aleatorios de funciones hash.

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `num_hashes` | `int` | requerido | Número de funciones hash |
| `seed` | `int` | `42` | Semilla aleatoria para reproducibilidad |

**Retorna:** `List[Tuple[int, int]]` - Lista de parámetros (a, b)

#### `minhash_signature(shingle_ids, hash_params, num_buckets=LARGE_PRIME)`

Calcula la firma MinHash para un documento.

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `shingle_ids` | `Set[int]` | requerido | Conjunto de IDs de shingles |
| `hash_params` | `List[Tuple]` | requerido | Parámetros de funciones hash |
| `num_buckets` | `int` | `LARGE_PRIME` | Conteo de buckets hash |

**Retorna:** `List[int]` - Firma MinHash

**Ejemplo:**
```python
from src.minhash import generate_hash_params, minhash_signature

params = generate_hash_params(100)
sig = minhash_signature({1, 5, 10, 15}, params)
# Retorna: [23451, 8923, 45123, ...] (100 enteros)
```

#### `estimate_similarity(sig_a, sig_b)`

Estima similitud Jaccard desde firmas.

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `sig_a` | `List[int]` | Primera firma |
| `sig_b` | `List[int]` | Segunda firma |

**Retorna:** `float` - Similitud estimada [0, 1]

---

### lsh.py

#### `lsh_candidates(signatures_rdd, num_bands)`

Encuentra pares candidatos usando banding LSH.

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `signatures_rdd` | `RDD[(id, signature)]` | Firmas de documentos |
| `num_bands` | `int` | Número de bandas |

**Retorna:** `RDD[(id1, id2)]` - Pares candidatos

**Ejemplo:**
```python
from src.lsh import lsh_candidates

# signatures_rdd: RDD de (doc_id, lista_de_firma)
candidates = lsh_candidates(signatures_rdd, num_bands=20)
# Retorna: RDD de pares (doc_id_1, doc_id_2)
```

#### `compute_threshold(num_bands, rows_per_band)`

Calcula umbral teórico de similitud.

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `num_bands` | `int` | Número de bandas |
| `rows_per_band` | `int` | Filas por banda |

**Retorna:** `float` - Umbral donde P(candidato) = 0.5

---

### jaccard.py

#### `jaccard_similarity(set_a, set_b)`

Calcula similitud Jaccard exacta.

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `set_a` | `Set` | Primer conjunto |
| `set_b` | `Set` | Segundo conjunto |

**Retorna:** `float` - Similitud Jaccard [0, 1]

#### `all_pairs_similarity(docs_rdd)`

Calcula similitud para todos los pares de documentos (fuerza bruta).

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `docs_rdd` | `RDD[(id, Set)]` | Conjuntos de shingles de documentos |

**Retorna:** `RDD[((id1, id2), float)]` - Todos los pares con similitud

---

### pipeline.py

#### `LSHConfig` (dataclass)

Configuración para el pipeline LSH.

```python
@dataclass
class LSHConfig:
    shingle_size: int = 3        # k para k-shingles
    char_level: bool = True      # Shingles de caracter vs palabra
    num_hashes: int = 100        # Longitud de firma
    num_bands: int = 20          # Bandas LSH (n debe ser divisible por b)
    similarity_threshold: float = 0.5  # Umbral de salida
```

#### `LSHResult` (dataclass)

Resultado del pipeline LSH.

```python
@dataclass
class LSHResult:
    candidate_pairs: RDD       # Candidatos crudos de LSH
    verified_pairs: RDD        # Pares sobre el umbral
    num_candidates: int        # Conteo de candidatos
    num_verified: int          # Conteo verificado
    config: LSHConfig          # Configuración usada
```

#### `run_lsh_pipeline(docs_rdd, config)`

Ejecuta el pipeline LSH completo.

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `docs_rdd` | `RDD[(id, text)]` | Documentos de entrada |
| `config` | `LSHConfig` | Configuración del pipeline |

**Retorna:** `LSHResult` - Resultados del pipeline

---

## 3. Opciones de Configuración

### Selección de Parámetros LSH

| Similitud Objetivo | Bandas (b) | Filas (r) | Notas |
|--------------------|------------|-----------|-------|
| ≥ 0.9 | 5 | 20 | Muy estricto |
| ≥ 0.7 | 10 | 10 | Estricto |
| ≥ 0.5 | 20 | 5 | **Recomendado** |
| ≥ 0.3 | 50 | 2 | Permisivo |

### Consideraciones de Memoria

| Tamaño del Corpus | Longitud de Firma Recomendada | Memoria por Doc |
|-------------------|-------------------------------|-----------------|
| < 10K | 100 | 400 bytes |
| 10K - 100K | 100 | 400 bytes |
| 100K - 1M | 50-100 | 200-400 bytes |
| > 1M | 50 | 200 bytes |

### Configuración de Spark

```python
spark = SparkSession.builder \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()
```

---

## 4. Optimización de Rendimiento

### Análisis de Cuellos de Botella

| Etapa | Cuello de Botella | Mitigación |
|-------|-------------------|------------|
| Shingling | I/O | Aumentar particiones |
| MinHash | CPU | Más ejecutores |
| LSH Banding | Shuffle | Ajustar particiones |
| Verificación | Memoria | Broadcast de shingles |

### Optimizaciones Implementadas

1. **Variables Broadcast**: Parámetros hash y vocabulario son broadcast a todos los workers

```python
hash_params_bc = sc.broadcast(hash_params)
vocab_bc = sc.broadcast(vocab)
```

2. **Ajuste de Particiones**: Los documentos son reparticionados según el tamaño del corpus

```python
optimal_partitions = max(200, num_docs // 1000)
docs_rdd = docs_rdd.repartition(optimal_partitions)
```

3. **Evaluación Lazy**: Las operaciones se encadenan sin materializar resultados intermedios

---

## 5. Estrategia de Testing

### Categorías de Tests

| Categoría | Cantidad | Propósito |
|-----------|----------|-----------|
| Tests unitarios | 40 | Correctitud de funciones individuales |
| Tests de integración | 10 | Interacciones entre módulos |
| Tests de propiedades | 5 | Invariantes matemáticas |

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Módulo específico
pytest tests/test_minhash.py -v

# Con coverage
pytest tests/ --cov=src --cov-report=html

# Solo smoke tests (rápido)
pytest tests/ -v -m smoke
```

### Casos de Test Clave

```python
# Shingling: entrada vacía
def test_empty_text_returns_empty_set():
    assert text_to_shingles("") == set()

# MinHash: longitud de firma
def test_signature_length_matches_num_hashes():
    params = generate_hash_params(100)
    sig = minhash_signature({1, 2, 3}, params)
    assert len(sig) == 100

# LSH: documentos idénticos son candidatos
def test_identical_docs_become_candidates():
    # ... crea docs idénticos, verifica que son candidatos

# Jaccard: límites de similitud
def test_jaccard_between_zero_and_one():
    sim = jaccard_similarity({1, 2}, {2, 3})
    assert 0 <= sim <= 1
```

---

## 6. Guía de Despliegue

### Desarrollo Local

```bash
# Setup
conda env create -f environment.yml
conda activate spark-text-similarity

# Verificar
make test-smoke
```

### Clúster de Producción

```bash
# Enviar a clúster Spark
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

### Docker (Opcional)

```dockerfile
FROM openjdk:17-slim

RUN pip install pyspark==3.5.0
COPY . /app
WORKDIR /app

CMD ["python", "scripts/run_pipeline.py", "--demo"]
```

### Pipeline CI/CD

El workflow de GitHub Actions:

1. **Matrix Testing**: Python 3.9, 3.10, 3.11
2. **Setup de Java**: OpenJDK 17
3. **Smoke Tests**: Subconjunto rápido para CI
4. **Tests Completos**: Solo en rama main

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

## Apéndice: Constantes

```python
# src/minhash.py
LARGE_PRIME = 2147483647  # 2^31 - 1 (primo de Mersenne)
MAX_HASH = 2**31 - 1

# src/lsh.py
DEFAULT_BANDS = 20
DEFAULT_SIGNATURE_LENGTH = 100
```

---

*Para derivaciones matemáticas, ver [Fórmulas Matemáticas](./MATHEMATICAL_FORMULAS.md).*

**English**: [View documentation in English](../en/)
