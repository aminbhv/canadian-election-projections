"""Convert the raw source files in data/raw into the tidy CSVs the model reads.

Run from the repository root:  python scripts/build_data.py

Output format (one row per riding x party):
    riding_id, riding_name, province, party, votes

See data/SOURCES.md for where each raw file came from.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from election.config import PARTIES, PROCESSED_DIR, PROVINCE_BY_CODE  # noqa: E402

RAW = ROOT / "data" / "raw"

# results_2025.json stores parties as integer indexes of this enum.
PARTY_ENUM_2025 = ["LPC", "CPC", "NDP", "BQ", "GPC", "PPC"]


def _province(riding_id: int) -> str:
    return PROVINCE_BY_CODE[riding_id // 1000]


def _party_2021(code: str) -> str:
    return code if code in PARTIES else "OTH"  # "Ind" and "OTH" both become OTH


def build_2021() -> list[dict]:
    raw = json.loads((RAW / "results_2021_transposed.json").read_text(encoding="utf-8"))
    rows = []
    for riding in raw:
        rid = int(riding["ridingCode"])
        votes = {p: 0 for p in PARTIES}
        for entry in riding["voteDistribution"]:
            votes[_party_2021(entry["partyCode"])] += int(entry["votes"])
        for party in PARTIES:
            rows.append(
                {
                    "riding_id": rid,
                    "riding_name": riding["ridingName_EN"],
                    "province": _province(rid),
                    "party": party,
                    "votes": votes[party],
                }
            )
    return rows


def build_2025() -> list[dict]:
    raw = json.loads((RAW / "results_2025.json").read_text(encoding="utf-8"))
    names = {int(r["id"]): r["name"] for r in json.loads((RAW / "ridings_2023_order.json").read_text(encoding="utf-8"))}
    rows = []
    for riding in raw:
        rid = int(riding["ridingId"])
        votes = {p: 0 for p in PARTIES}
        for cand in riding["candidates"]:
            idx = cand["party"]
            party = PARTY_ENUM_2025[idx] if idx < len(PARTY_ENUM_2025) else "OTH"
            votes[party] += int(cand["votes"])
        for party in PARTIES:
            rows.append(
                {
                    "riding_id": rid,
                    "riding_name": names[rid],
                    "province": _province(rid),
                    "party": party,
                    "votes": votes[party],
                }
            )
    return rows


def write(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: (r["riding_id"], PARTIES.index(r["party"])))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path.relative_to(ROOT)} ({len(rows)} rows)")


def main() -> None:
    write(build_2021(), PROCESSED_DIR / "results_2021_transposed.csv")
    write(build_2025(), PROCESSED_DIR / "results_2025.csv")


if __name__ == "__main__":
    main()
