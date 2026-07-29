NAME := fly-in

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

SYSTEM_PYTHON := python3
MAIN := main.py

MAP ?= maps/easy/01_linear_path.txt

.PHONY: install run graphics debug clean fclean re lint lint-strict

install:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(SYSTEM_PYTHON) -m venv $(VENV); \
	fi
	$(PIP) install -r requirements.txt

run: install
	$(PYTHON) $(MAIN) $(MAP)

graphics: install
	$(PYTHON) $(MAIN) $(MAP) --graphics

debug: install
	$(PYTHON) -m pdb $(MAIN) $(MAP)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf .ruff_cache

fclean: clean
	rm -rf $(VENV)

re: fclean install

lint: install
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict: install
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . --strict
