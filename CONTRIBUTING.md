# Contributing to tokencost

## Quick Start

```bash
git clone https://github.com/AbdullahTarakji/tokencost.git
cd tokencost
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Development Workflow

1. Fork → feature branch from `develop` → PR against `develop`
2. Run `ruff check src/ tests/` and `pytest` before pushing
3. Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`

## License

MIT — contributions licensed under the same.
