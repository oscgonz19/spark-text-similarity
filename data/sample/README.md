# Sample Data

This directory contains sample datasets for testing and demonstration.

## Synthetic Data

The project includes a data generator (`src/data_generator.py`) that creates synthetic documents with controlled similarity levels. This ensures:

1. **Clear licensing**: All generated text is original and released under CC0
2. **Ground truth**: We know exactly which documents should be similar
3. **Reproducibility**: Same seed produces same corpus

## Usage

Generate sample data programmatically:

```python
from pyspark.sql import SparkSession
from src.data_generator import create_sample_rdd, get_tiny_sample

spark = SparkSession.builder.master("local[*]").getOrCreate()
sc = spark.sparkContext

# Tiny sample for quick testing (5 documents)
tiny_rdd = get_tiny_sample(sc)

# Larger sample with controlled similar pairs
docs_rdd, expected_pairs = create_sample_rdd(
    sc,
    num_documents=100,
    doc_length=50,        # words per document
    num_similar_pairs=20,
    seed=42
)
```

## Input Format

If providing your own documents, use tab-separated format:

```
doc_id<TAB>document text here
```

Example (`documents.txt`):
```
doc001	The quick brown fox jumps over the lazy dog.
doc002	Pack my box with five dozen liquor jugs.
doc003	How vexingly quick daft zebras jump!
```

Load with:
```bash
python scripts/run_pipeline.py --input data/sample/documents.txt
```
