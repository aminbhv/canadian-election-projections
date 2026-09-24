# Data sources

All data needed to reproduce every result is committed in `data/`. The raw files are
converted into tidy CSVs by `python scripts/build_data.py`.

| File | Contents | Source |
|---|---|---|
| `raw/results_2021_transposed.json` | 2021 results re-computed on the 343-riding map | [ThreeFortyThree-Canada/elections-canada-mcp-server](https://github.com/ThreeFortyThree-Canada/elections-canada-mcp-server) (MIT), derived from Elections Canada's *Transposition of Votes from the 44th General Election to the 2023 Representation Orders* ([official dataset](https://open.canada.ca/data/en/dataset/08c4ffbc-c513-41a4-b741-d35b41b50c22)) |
| `raw/results_2025.json`, `raw/ridings_2023_order.json` | 2025 official results by riding, riding names | [smithbower/CanadianElectionSimulator](https://github.com/smithbower/CanadianElectionSimulator) (MIT), derived from Elections Canada's official GE45 results |
| `processed/polls_2025_final_week.csv` | Latest national poll from each firm, April 21–27, 2025 | Wikipedia, *Opinion polling for the 2025 Canadian federal election* (accessed 2026-09-24) |
| `processed/polls_latest.csv` | Recent national polls, September 2026 | Wikipedia, *Opinion polling for the 46th Canadian federal election* (accessed 2026-09-24) |
| `canada_regions.geojson` | Region outlines for the dashboard map | Carried over from the original course project; origin not documented |

## Why the 2021 results are "transposed"

Riding boundaries changed between 2021 (338 ridings) and 2025 (343 ridings). Elections Canada
estimated how each 2021 vote would have been counted under the new boundaries, using voter
addresses. Using those estimates means the 2021 baseline and the 2025 results describe the
same 343 ridings, so a 2021 → 2025 backtest compares like with like.

## Validation

These checks run in `tests/test_data.py` on every CI build:

- 2025 seat totals are exactly the official 169 LPC / 144 CPC / 22 BQ / 7 NDP / 1 GPC.
- 2025 and 2021 national vote shares match official results to within 0.02 points.
- Six 2021 transposed riding values match Elections Canada's `transposition_343_fed.csv` exactly.
- The Bloc Québécois has zero votes outside Quebec in both years.

The 2025 file was also cross-checked against an independent dataset
([QUARK88/can2025](https://github.com/QUARK88/can2025)): all 343 riding winners agree, and
party shares agree to within about one point (the gap comes from rounding in that dataset).

## Updating the polls

Add rows to `processed/polls_latest.csv`: one row per poll, percentages per party, with the
end date of fieldwork. The model averages the most recent poll from each firm, so daily
rolling polls from one firm cannot dominate the average. Leave a party at 0 if the poll did
not report it.

## Third-party licenses

Both redistributed raw datasets are MIT-licensed. Their full license texts are included, as
the MIT license requires:

- `raw/results_2021_transposed.json`: `raw/licenses/LICENSE-ThreeFortyThree-Canada.txt`
- `raw/results_2025.json`, `raw/ridings_2023_order.json`: `raw/licenses/LICENSE-smithbower.txt`
