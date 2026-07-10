PYTHON = python3
MAIN_SCRIPT = flyin.py

.PHONY: install run debug clean lint lint-strict

install:
	pip install -r requirements.txt

run:
	@if [ "$(filter-out run,$(MAKECMDGOALS))" != "" ]; then \
		echo "[ERROR] - Use 'make run ARGS=<file.txt>'"; \
		exit 1; \
	fi
	$(PYTHON) $(MAIN_SCRIPT) $(ARGS)

debug:
	$(PYTHON) -m pdb $(MAIN_SCRIPT)

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8; mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8; mypy . --strict