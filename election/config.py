"""Constants shared across the package: parties, geography, and paths."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = ROOT / "reports"

RESULTS_2021 = PROCESSED_DIR / "results_2021_transposed.csv"
RESULTS_2025 = PROCESSED_DIR / "results_2025.csv"
POLLS_2025_FINAL_WEEK = PROCESSED_DIR / "polls_2025_final_week.csv"
POLLS_LATEST = PROCESSED_DIR / "polls_latest.csv"
REGIONS_GEOJSON = DATA_DIR / "canada_regions.geojson"

# Party order is fixed everywhere: arrays have one column per party in this order.
PARTIES = ("LPC", "CPC", "NDP", "BQ", "GPC", "PPC", "OTH")
PARTY_NAMES = {
    "LPC": "Liberal",
    "CPC": "Conservative",
    "NDP": "NDP",
    "BQ": "Bloc Québécois",
    "GPC": "Green",
    "PPC": "People's Party",
    "OTH": "Other / Independent",
}
PARTY_COLORS = {
    "LPC": "#d71920",
    "CPC": "#1a4782",
    "NDP": "#f58220",
    "BQ": "#33b2cc",
    "GPC": "#3d9b35",
    "PPC": "#4b2e83",
    "OTH": "#8c8c8c",
}

# Elections Canada riding codes start with a two-digit province code.
PROVINCE_BY_CODE = {
    10: "NL",
    11: "PE",
    12: "NS",
    13: "NB",
    24: "QC",
    35: "ON",
    46: "MB",
    47: "SK",
    48: "AB",
    59: "BC",
    60: "YT",
    61: "NT",
    62: "NU",
}

# Polls are usually reported for these regions, so swing is applied per region.
REGION_BY_PROVINCE = {
    "NL": "ATL",
    "PE": "ATL",
    "NS": "ATL",
    "NB": "ATL",
    "QC": "QC",
    "ON": "ON",
    "MB": "PRA",
    "SK": "PRA",
    "AB": "AB",
    "BC": "BC",
    "YT": "TER",
    "NT": "TER",
    "NU": "TER",
}
REGIONS = ("ATL", "QC", "ON", "PRA", "AB", "BC", "TER")
REGION_NAMES = {
    "ATL": "Atlantic Canada",
    "QC": "Quebec",
    "ON": "Ontario",
    "PRA": "Sask. & Man.",
    "AB": "Alberta",
    "BC": "British Columbia",
    "TER": "Territories",
}

TOTAL_SEATS = 343  # 2023 Representation Order, in force since the 2025 election
MAJORITY_THRESHOLD = TOTAL_SEATS // 2 + 1  # 172
