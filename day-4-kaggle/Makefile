export PATH := $(CURDIR)/.venv/Scripts:$(PATH)

.PHONY: install playground generate-traces grade

install:
	python -m venv .venv
	.venv\Scripts\python -m pip install --upgrade pip
	.venv\Scripts\pip install -e .
	.venv\Scripts\pip install uv

playground:
	.venv\Scripts\agents-cli playground

generate-traces:
	.venv\Scripts\python tests/eval/generate_traces.py

grade:
	.venv\Scripts\agents-cli eval grade --traces artifacts/traces/generated_traces.json --config tests/eval/eval_config.yaml
