# Documentation / Documentación

Complete documentation for the spark-text-similarity project.

Documentación completa para el proyecto spark-text-similarity.

---

## Language / Idioma

| Language | Folder | Description |
|----------|--------|-------------|
| **English** | [docs/en/](./en/) | All documentation in English |
| **Español** | [docs/es/](./es/) | Toda la documentación en Español |

---

## English Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| [Case Study](./en/CASE_STUDY.md) | Complete portfolio case study | General |
| [Executive Summary](./en/EXECUTIVE_SUMMARY.md) | High-level overview with architecture diagram | Recruiters / Managers |
| [Technical Appendix](./en/TECHNICAL_APPENDIX.md) | Detailed technical documentation | Tech Leads / Engineers |
| [Pipeline Explained](./en/PIPELINE_EXPLAINED.md) | How the similarity pipeline works | Data Scientists / ML Engineers |
| [Mathematical Formulas](./en/MATHEMATICAL_FORMULAS.md) | MinHash, LSH, and probability derivations | Statisticians / Quants |

---

## Documentación en Español

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| [Caso de Estudio](./es/CASE_STUDY.md) | Caso de estudio completo para portafolio | General |
| [Resumen Ejecutivo](./es/EXECUTIVE_SUMMARY.md) | Vista general con diagrama de arquitectura | Reclutadores / Gerentes |
| [Apéndice Técnico](./es/TECHNICAL_APPENDIX.md) | Documentación técnica detallada | Líderes Técnicos / Ingenieros |
| [Pipeline Explicado](./es/PIPELINE_EXPLAINED.md) | Cómo funciona el pipeline de similitud | Científicos de Datos / Ingenieros ML |
| [Fórmulas Matemáticas](./es/MATHEMATICAL_FORMULAS.md) | Derivaciones de MinHash, LSH y probabilidad | Estadísticos / Quants |

---

## Directory Structure / Estructura de Directorios

```
docs/
├── README.md           # This file / Este archivo
├── en/                 # English documentation
│   ├── CASE_STUDY.md
│   ├── EXECUTIVE_SUMMARY.md
│   ├── TECHNICAL_APPENDIX.md
│   ├── PIPELINE_EXPLAINED.md
│   └── MATHEMATICAL_FORMULAS.md
└── es/                 # Documentación en español
    ├── CASE_STUDY.md
    ├── EXECUTIVE_SUMMARY.md
    ├── TECHNICAL_APPENDIX.md
    ├── PIPELINE_EXPLAINED.md
    └── MATHEMATICAL_FORMULAS.md
```

---

## Quick Start / Comenzar

```bash
# Clone and setup / Clonar y configurar
git clone https://github.com/yourusername/spark-text-similarity.git
cd spark-text-similarity
conda env create -f environment.yml
conda activate spark-text-similarity

# Run demo / Ejecutar demo
make run-demo

# Run tests / Ejecutar pruebas
make test
```
