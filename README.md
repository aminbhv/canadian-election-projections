# 🇨🇦 Canadian Federal Election Seat Projections

An interactive Monte Carlo simulation dashboard that projects Canadian federal election seat outcomes by province. Scrapes live polling data, adjusts it using historical voter transition patterns, and visualizes results in a multi-tab Dash app.

> Built with Python · Dash · Plotly · Selenium · NetworkX · pandas

---

## How It Works

1. **Scrape** — Selenium fetches current provincial polling data from 338Canada
2. **Adjust** — A NetworkX directed graph of voter transitions (2015 → 2019 → 2021) shifts raw polls to account for historical swing patterns
3. **Simulate** — 1,000 Monte Carlo trials allocate seats per province under First Past the Post (FPTP) rules (~667 trials/sec)
4. **Visualize** — Results render as an interactive choropleth map, seat bar chart, voter transition graph, and side-by-side comparison

---

## Features

- 📊 **Live polling ingestion** via headless Selenium scraper
- 🗳️ **FPTP seat allocation** modelled as a recursive election tree (country → province → seat)
- 🔀 **Voter transition graph** built from 2015/2019/2021 historical results to adjust current polling
- 🎲 **Monte Carlo simulation** — 1,000 trials to estimate majority/minority/no-win probabilities per party
- 🗺️ **Choropleth map** of projected seats by province
- ⚡ **Performance optimizations** — polling cached, results batched and precomputed

---

## Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/aminbhv/canadian-election-projections.git
cd canadian-election-projections

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Run the dashboard
python dashboard.py
```

Then open the URL printed in your terminal (e.g. `http://127.0.0.1:8050/`).

> **Note:** The first run fetches live polling via a headless browser and may take 30–60 seconds depending on your network.

---

## Project Structure

```
canadian-election-projections/
├── dashboard.py          # Dash app layout and callbacks
├── election_model.py     # Monte Carlo simulation + RegionNode tree
├── scraper.py            # Selenium-based live polling scraper
├── graph.py              # Voter transition graph (NetworkX)
├── visualization.py      # Plotly chart builders (choropleth, bar chart)
├── data_loader.py        # Historical CSV loader
├── config.py             # Seat counts, party colours, constants
├── 2015.csv              # 2015 federal election results by province
├── 2019.csv              # 2019 federal election results by province
├── 2021.csv              # 2021 federal election results by province
├── canada_provinces.geojson  # GeoJSON for choropleth map
├── requirements.txt
├── .github/workflows/    # GitHub Actions CI (lint via Ruff)
└── LICENSE               # MIT
```

---

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| **Province Map** | Choropleth map of projected seat winners by province |
| **Seat Bar Chart** | Bar chart of projected seat distribution across parties |
| **Voter Transition Graph** | NetworkX graph of historical voter flows (2015→2019→2021) |
| **Compare Predictions** | Side-by-side: with vs. without voter transition adjustment |

---

## Validation

Projections were back-tested against the 2015, 2019, and 2021 federal election results to verify model accuracy.

---

## CI

A lightweight GitHub Actions workflow runs on every push to lint the codebase with [Ruff](https://github.com/astral-sh/ruff). Full Selenium/Dash execution is disabled in CI to avoid flaky headless-browser issues.

---

## License

[MIT](LICENSE)
