# Resumen Ejecutivo

## Detección Escalable de Similitud de Documentos con Apache Spark

---

## El Problema de Negocio

Las organizaciones con grandes colecciones de documentos enfrentan un desafío común: **encontrar documentos similares o duplicados de manera eficiente**. Esto aplica a:

| Industria | Caso de Uso | Impacto |
|-----------|-------------|---------|
| **Editorial** | Detección de plagio | Integridad académica |
| **Medios** | Deduplicación de noticias | Experiencia de usuario |
| **Legal** | Similitud de contratos | Debida diligencia |
| **E-commerce** | Emparejamiento de productos | Calidad del catálogo |

### El Desafío de Escala

El enfoque ingenuo compara cada par de documentos:

```
1,000 documentos    →     500,000 comparaciones
100,000 documentos  →   5,000,000,000 comparaciones
1,000,000 documentos → 500,000,000,000 comparaciones
```

**Con 1 millón de documentos, fuerza bruta toma casi 6 días de cómputo.**

---

## Nuestra Solución

Construimos un **pipeline de Locality-Sensitive Hashing (LSH)** que:

1. **Reduce la complejidad** de O(n²) a aproximadamente O(n)
2. **Escala horizontalmente** usando Apache Spark
3. **Mantiene alta precisión** con 100% de precisión y 85% de recall

### Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     PIPELINE DE SIMILITUD DE DOCUMENTOS                        │
│                                                                                 │
│   ┌─────────────┐                                                              │
│   │   Corpus    │                                                              │
│   │     de      │                                                              │
│   │ Documentos  │                                                              │
│   │  (N docs)   │                                                              │
│   └──────┬──────┘                                                              │
│          │                                                                      │
│          ▼                                                                      │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐ │
│   │             │     │             │     │             │     │             │ │
│   │  SHINGLING  │────▶│   MINHASH   │────▶│     LSH     │────▶│ VERIFICAR   │ │
│   │             │     │             │     │             │     │             │ │
│   │ Convertir a │     │  Comprimir  │     │  Agrupar    │     │  Calcular   │ │
│   │  k-gramas   │     │  firmas     │     │  similares  │     │   Jaccard   │ │
│   │             │     │             │     │             │     │   exacto    │ │
│   └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘ │
│          │                   │                   │                   │         │
│          ▼                   ▼                   ▼                   ▼         │
│    Conjuntos de          Firmas             Pares              Resultados      │
│     shingles           compactas          candidatos          verificados      │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                        CLÚSTER APACHE SPARK                                    │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│   │Worker 1 │  │Worker 2 │  │Worker 3 │  │Worker 4 │  │Worker N │             │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Resultados Clave

### Rendimiento del Benchmark

| Métrica | Valor |
|---------|-------|
| **Corpus de prueba** | 100 documentos |
| **Pares realmente similares** | 26 pares (similitud ≥ 0.5) |
| **Pares encontrados** | 22 pares (85% recall) |
| **Falsos positivos** | 0 (100% precisión) |
| **Puntaje F1** | 0.917 |
| **Reducción de comparaciones** | 84% menos comparaciones |

### Proyección de Escalabilidad

| Tamaño del Corpus | Fuerza Bruta | Nuestra Solución | Ahorro |
|-------------------|--------------|------------------|--------|
| 1,000 docs | 500K comparaciones | 80K | 84% |
| 100,000 docs | 5 mil millones | 780 millones | 84% |
| 1,000,000 docs | 500 mil millones | 78 mil millones | 84% |

---

## Stack Tecnológico

| Componente | Tecnología | Por qué |
|------------|------------|---------|
| **Procesamiento** | Apache Spark 3.5 | Estándar de la industria para cómputo distribuido |
| **Lenguaje** | Python 3.11 | Ecosistema de ciencia de datos |
| **Algoritmo** | MinHash + LSH | Enfoque probabilístico probado |
| **Testing** | pytest (55 tests) | Calidad lista para producción |
| **CI/CD** | GitHub Actions | Aseguramiento de calidad automatizado |

---

## Por qué Esto Importa

### Excelencia Técnica

- **Sofisticación algorítmica**: Implementa estructuras de datos probabilísticas de vanguardia
- **Calidad de producción**: 55 pruebas unitarias, pipeline CI/CD, documentación completa
- **Diseño escalable**: Escalable horizontalmente con Spark

### Valor de Negocio

- **Reducción de costos**: 84% menos cómputo = menores costos de nube
- **Tiempo a resultados**: Horas en lugar de días para corpus grandes
- **Precisión**: Cero falsos positivos mediante paso de verificación

---

## Comenzar

```bash
# Clonar y configurar
git clone https://github.com/yourusername/spark-text-similarity.git
cd spark-text-similarity
conda env create -f environment.yml
conda activate spark-text-similarity

# Ejecutar demo
make run-demo

# Ejecutar pruebas
make test
```

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [Caso de Estudio](./CASE_STUDY.md) | Recorrido técnico completo |
| [Apéndice Técnico](./TECHNICAL_APPENDIX.md) | Detalles de implementación |
| [Pipeline Explicado](./PIPELINE_EXPLAINED.md) | Guía paso a paso del algoritmo |
| [Fórmulas Matemáticas](./MATHEMATICAL_FORMULAS.md) | Derivaciones de probabilidad |

**English**: [View documentation in English](../en/)

---

*Este proyecto demuestra experiencia en sistemas distribuidos, diseño de algoritmos e ingeniería de producción.*
