# Canadian Federal Election Polling & Seat Projections 🇨🇦

Interactive Monte Carlo simulation and dashboard for Canadian federal election projections.  
Scrapes live provincial polling, adjusts with historical voter swings, and visualizes seat outcomes.

## Demo (local)
1. Create a virtualenv and install deps
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the app
   ```bash
   python dashboard.py
   ```
   Then open the printed local URL (e.g., http://127.0.0.1:8050/).

> Note: Selenium opens a headless browser to pull live polling; the first run may take ~30–60s depending on network.

## Features
- Tree-based seat allocation per province (FPTP)
- Voter-transition **graph** from 2015→2019→2021 to adjust current polling
- **1,000** simulation trials for majority/minority probabilities
- **Dash** app with tabs: Map, Seat Distribution, Voter Transitions, and Compare Predictions

## Project Structure
```
canadian-federal-election-polling-&-seat-projections/
├─ <src modules>
├─ docs/                # images/figures for README (optional)
├─ tests/               # add unit tests if needed
├─ .github/workflows/ci.yml
├─ requirements.txt
├─ .gitignore
├─ LICENSE
└─ README.md
```

## Requirements
Listed in `requirements.txt`; core libraries include Selenium, pandas, networkx, plotly, and dash.

## Notes on CI
This repo includes a lightweight GitHub Actions workflow that lints and sanity-checks syntax.  
Running the full Selenium/Dash app in CI is disabled by default to avoid flaky headless-browser issues.

## License
MIT — see `LICENSE`.

---

Academic context and detailed design are in the included PDF project report.
