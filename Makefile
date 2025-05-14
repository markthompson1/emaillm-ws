VENV ?= .venv
PY   ?= $(VENV)/bin/python
PIP  ?= $(VENV)/bin/pip

.PHONY: venv test dev clean

venv:
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements-dev.txt
	@# ensure PYTHONPATH persists for every activate
	@if ! grep -q "export PYTHONPATH" $(VENV)/bin/activate; then \
	  echo '\nexport PYTHONPATH="$$VIRTUAL_ENV/../src:$$PYTHONPATH"' >> $(VENV)/bin/activate; \
	fi

test:
	source $(VENV)/bin/activate && pytest -q

dev:
	source $(VENV)/bin/activate && uvicorn emaillm:app --app-dir src --reload

clean:
	rm -rf $(VENV) .pytest_cache .coverage **/__pycache__
