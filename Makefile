PYTHON = python3
MAIN_SCRIPT = flyin.py

.PHONY: install run debug clean lint lint-strict clean-venv

install:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

run:
	@if [ "$(filter-out run,$(MAKECMDGOALS))" != "" ]; then \
		echo "[ERROR] - Use 'make run ARGS=<file.txt>'"; \
		exit 1; \
	fi
	./venv/bin/$(PYTHON) $(MAIN_SCRIPT) $(ARGS)

debug:
	./venv/bin/$(PYTHON) -m pdb $(MAIN_SCRIPT)

clean:
	rm -rf __pycache__
	rm -rf .mypy_cache

clean-venv:
	rm -rf venv

lint:
	flake8; mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8; mypy . --strict