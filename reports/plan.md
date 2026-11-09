# Plan: EnvSieve — Zero-Dependency Environment Variable & Template Drift Gate

Date: 2026-11-09 (IST)  
Stage: Plan  
Project: **EnvSieve**

---

## 1. Success Metrics

1. **Extraction Accuracy**: 100% extraction of string literal environment variable accesses across Python AST (`os.environ`, `os.getenv`) and JS/TS (`process.env`, `import.meta.env`).
2. **Speed**: Sub-30ms execution on standard repositories, suitable for zero-latency git pre-commit hooks.
3. **Template Discovery**: Automatic recognition of standard template filenames (`.env.example`, `.env.template`, `.env.sample`, `example.env`, `Dockerfile`).
4. **Actionable Feedback**: Precise file, line number, statement, and recommendation (e.g. `Add REDIS_URL to .env.example`).
5. **Deterministic Exit Codes**: Returns code 1 when missing variables or secret values are found; returns 0 when clean.

---

## 2. Minimal Architecture

Directory structure inside `projects/20261109-053749-developer-and-engineering-pain-points`:

```
src/
└── envsieve/
    ├── __init__.py           # Package exports & version
    ├── __main__.py           # python -m envsieve
    ├── cli.py                # Command-line flags and exit code orchestration
    ├── core.py               # Audit engine & reconciliation
    ├── extractors/
    │   ├── __init__.py
    │   ├── python_extractor.py # Python AST visitor for os.environ / os.getenv
    │   └── js_extractor.py     # Regex tokenizer for process.env / import.meta.env
    ├── parsers/
    │   ├── __init__.py
    │   ├── env_parser.py       # Parses .env.example, .env.template
    │   └── docker_parser.py    # Parses Dockerfile ENV & ARG statements
    └── reporter.py           # Terminal ANSI, JSON, and Markdown cards
```

---

## 3. Dependency Inventory

- **Runtime**: Pure Python 3.10+ standard library (`ast`, `re`, `pathlib`, `json`, `argparse`, `sys`, `subprocess`, `os`).
- **Zero Third-Party Packages**: No `pip install` required.
- **Offline & Private**: Never transmits variables or project code across the network.

---

## 4. Security & Privacy Notes

- Pure static analysis: never executes user code.
- Scans template files for leaked credentials matching high-confidence secret patterns (e.g., `sk_live_`, `ghp_`, `AKIA[0-9A-Z]{16}`, private keys).
- Redacts sensitive variable values in reports by default.

---

## 5. Task Breakdown

1. **Extractors**: Implement `python_extractor.py` and `js_extractor.py`.
2. **Parsers**: Implement `env_parser.py` (key-value parsing, comment stripping) and `docker_parser.py`.
3. **Core Engine**: Implement `core.py` to reconcile code references vs template declarations, detecting missing keys, zombie keys, and secret values.
4. **CLI & Reporters**: Implement `cli.py`, `reporter.py` with `--diff`, `--strict`, `--output-json`, `--output-md`.
5. **Test Suite**: Comprehensive unit tests for AST extraction, template parsing, and CLI edge cases.
6. **Documentation & Demo**: Write `README.md`, `LICENSE`, and runnable `demo.py`.
7. **Showcase Assets**: Invoke `image-generator` subagent to generate explanatory AI visual diagram for `assets/`, plus a truthful terminal SVG demo.

---

## 6. Executable Acceptance Tests

1. **Python Missing Key**: Detects `os.environ["API_KEY"]` missing from `.env.example`.
2. **JS/TS Missing Key**: Detects `process.env.DB_PASSWORD` missing from `.env.example`.
3. **Zombie Key**: Flags `OLD_UNUSED_FLAG` in `.env.example` not referenced in code.
4. **Secret Value Warning**: Flags live secret string in `.env.example`.
5. **Clean Repository**: Returns exit code 0 when all keys match.
