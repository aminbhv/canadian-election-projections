"""
Canadian Election Simulator - Historical Data Loader

Copyright (c) 2025 Amin Behbudov, Fares Abdulmajeed Alabdulhadi, Tahmid Wasif Zaman, Dimural Murat

This module handles loading and cleaning historical election data from CSV files.
"""

from typing import Dict, Tuple

import pandas as pd

from config import PROVINCE_MAP, VALID_PARTIES


def clean_and_merge(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Clean and aggregate constituency-level election data into provincial totals.

    Args:
        df (pd.DataFrame): Raw election data with constituencies as columns.

    Returns:
        Dict[str, Dict[str, float]]: Province-keyed dict of normalized party vote shares.
    """
    cleaned: Dict[str, Dict[str, float]] = {}

    for col in df.columns:
        prov = None
        for group, names in PROVINCE_MAP.items():
            if isinstance(names, list) and any(name in col for name in names):
                prov = group
            elif isinstance(names, str) and names in col:
                prov = group
        if prov is None:
            continue

        for party, val in df[col].items():
            norm = party.strip().upper()
            if "LIBERTARIAN" in norm or "PARTI LIBERTARIEN" in norm:
                norm = "OTH"
            elif norm not in VALID_PARTIES:
                norm = "OTH"

            if prov not in cleaned:
                cleaned[prov] = {}
            cleaned[prov][norm] = cleaned[prov].get(norm, 0) + val

    # Normalize each province's vote shares to sum to 1
    for prov in cleaned:
        total = sum(cleaned[prov].values())
        for key in cleaned[prov]:
            cleaned[prov][key] /= total

    return cleaned


def load_historical_data() -> Tuple[
    Dict[str, Dict[str, float]],
    Dict[str, Dict[str, float]],
    Dict[str, Dict[str, float]],
]:
    """
    Load and clean historical election data from CSV files.

    Returns:
        Tuple of (votes_2015, votes_2019, votes_2021), each a province-keyed
        dict of normalized party vote shares.
    """
    df_2015 = pd.read_csv("2015.csv", index_col=0)
    df_2019 = pd.read_csv("2019.csv", index_col=0)
    df_2021 = pd.read_csv("2021.csv", index_col=0)

    return (
        clean_and_merge(df_2015),
        clean_and_merge(df_2019),
        clean_and_merge(df_2021),
    )


if __name__ == "__main__":
    votes_2015, votes_2019, votes_2021 = load_historical_data()
    print("2015 Election Data Sample:")
    for province in list(votes_2015.keys())[:2]:
        print(f"  {province}: {votes_2015[province]}")
