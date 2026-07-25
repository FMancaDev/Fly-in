NAME := fly-in

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
AUTOPEP8 := $(VENV)/bin/autopep8

SYSTEM_PYTHON := python3.12
MAIN := main.py

MAP ?= maps/easy/01_linear_path.txt

SRC := $(shell find src -type f -name "*.py")
PY_FILES := $(MAIN) $(SRC)

.PHONY: all venv install run graphics check format test clean fclean re shell help

all: venv check

venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(SYSTEM_PYTHON) -m venv $(VENV); \
	fi

install: venv
	$(PIP) install --upgrade pip
	@if [ -f requirements.txt ]; then \
		$(PIP) install -r requirements.txt; \
	else \
		echo "requirements.txt not found"; \
	fi

run: venv
	$(PYTHON) $(MAIN) $(MAP)

graphics: venv
	$(PYTHON) $(MAIN) $(MAP) --graphics

check: venv
	$(PYTHON) -m py_compile $(PY_FILES)

format: venv
	@if [ ! -x "$(AUTOPEP8)" ]; then \
		$(PIP) install autopep8; \
	fi
	$(AUTOPEP8) --in-place --recursive src $(MAIN)

test: venv
	@if [ ! -x "$(PYTEST)" ]; then \
		$(PIP) install pytest; \
	fi
	$(PYTEST) -v

shell: venv
	@echo "Opening a shell with the virtual environment activated..."
	@bash -c 'source $(VENV)/bin/activate && exec bash'

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache

fclean: clean
	rm -rf $(VENV)
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

re: fclean all
