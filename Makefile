.PHONY: setup setup-dev test test-smoke test-cov run-demo run-experiments visualizations clean lint format help

# Default Python and pip
PYTHON ?= python3
PIP ?= pip3

# Directories
SRC_DIR = src
TEST_DIR = tests
SCRIPTS_DIR = scripts
REPORTS_DIR = reports
OUTPUT_DIR = output

help:
	@echo "spark-text-similarity - Makefile targets"
	@echo ""
	@echo "Setup:"
	@echo "  make setup        Install production dependencies"
	@echo "  make setup-dev    Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-smoke   Run smoke tests only (fast, for CI)"
	@echo "  make test-cov     Run tests with coverage report"
	@echo ""
	@echo "Running:"
	@echo "  make run-demo     Run pipeline with demo data"
	@echo "  make run-experiments  Run full experiment suite"
	@echo "  make visualizations   Generate documentation charts"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         Run linters (ruff, mypy)"
	@echo "  make format       Format code with black"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        Remove generated files"

# =============================================================================
# Setup
# =============================================================================

setup:
	$(PIP) install -e .

setup-dev:
	$(PIP) install -e ".[dev]"

# =============================================================================
# Testing
# =============================================================================

test:
	$(PYTHON) -m pytest $(TEST_DIR) -v

test-smoke:
	$(PYTHON) -m pytest $(TEST_DIR) -v -m smoke --tb=short

test-cov:
	$(PYTHON) -m pytest $(TEST_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

# =============================================================================
# Running
# =============================================================================

run-demo:
	$(PYTHON) $(SCRIPTS_DIR)/run_pipeline.py --demo

run-pipeline:
	$(PYTHON) $(SCRIPTS_DIR)/run_pipeline.py

run-experiments:
	@mkdir -p $(REPORTS_DIR)
	$(PYTHON) $(SCRIPTS_DIR)/run_experiments.py \
		--num-docs 50 \
		--doc-length 100 \
		--num-similar 15 \
		--output-dir $(REPORTS_DIR)

run-experiments-large:
	@mkdir -p $(REPORTS_DIR)
	$(PYTHON) $(SCRIPTS_DIR)/run_experiments.py \
		--num-docs 200 \
		--doc-length 150 \
		--num-similar 40 \
		--output-dir $(REPORTS_DIR)

visualizations:
	@echo "Generating visualizations..."
	@mkdir -p docs/images
	$(PYTHON) -c "from src.visualizations import generate_all_visualizations; generate_all_visualizations()"

# =============================================================================
# Code Quality
# =============================================================================

lint:
	$(PYTHON) -m ruff check $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	$(PYTHON) -m mypy $(SRC_DIR) --ignore-missing-imports

format:
	$(PYTHON) -m black $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	$(PYTHON) -m ruff check --fix $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)

# =============================================================================
# Cleanup
# =============================================================================

clean:
	rm -rf $(OUTPUT_DIR)
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf build dist
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-reports:
	rm -rf $(REPORTS_DIR)/*.csv
	rm -rf $(REPORTS_DIR)/*.md
