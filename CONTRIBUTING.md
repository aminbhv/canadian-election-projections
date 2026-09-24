# Contributing

1. Create a virtual environment and run `pip install -r requirements-dev.txt`.
2. Before pushing, run `ruff check .`, `ruff format .`, and `pytest`.
3. If you change the model or data, re-run `python -m election.backtest` and commit the updated
   `reports/` folder so the README and dashboard show current numbers.
4. If you change a raw data file, re-run `python scripts/build_data.py` and document the source in
   `data/SOURCES.md`.
