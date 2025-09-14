"""
Canadian Election Simulator - Historical Data Loader
Copyright (c) 2025 [Amin Behbudov, Fares Abdulmajeed Alabdulhadi, Tahmid Wasif Zaman, Dimural Murat]

This module handles loading and cleaning historical election data.
"""

from typing import Dict, Tuple
import pandas as pd
from config import PROVINCE_MAP, VALID_PARTIES


def clean_and_merge(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Cleans and transforms election data by merging constituencies into provinces.

    Args:
        df (pandas.DataFrame): DataFrame containing election data

    Returns:
        dict: Dictionary of cleaned provincial voting data with parties as percentages
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

    for prov in cleaned:
        total = sum(cleaned[prov].values())
        for key in cleaned[prov]:
            cleaned[prov][key] /= total
    return cleaned


def load_historical_data() -> Tuple[Dict[str, Dict[str, float]],
                                    Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
    """
    Loads and cleans historical election data from CSV files.

    Returns:
        tuple: A tuple containing (votes_2015, votes_2019, votes_2021)
    """
    df_2015 = pd.read_csv("2015.csv", index_col=0)
    df_2019 = pd.read_csv("2019.csv", index_col=0)
    df_2021 = pd.read_csv("2021.csv", index_col=0)

    data_2015 = clean_and_merge(df_2015)
    data_2019 = clean_and_merge(df_2019)
    data_2021 = clean_and_merge(df_2021)

    return data_2015, data_2019, data_2021


if __name__ == "__main__":
    # Test data loading
    votes_data_2015, votes_data_2019, votes_data_2021 = load_historical_data()
    print("2015 Election Data Sample:")
    for province in list(votes_data_2015.keys())[:2]:
        print(f"{province}: {votes_data_2015[province]}")


if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'extra-imports': [],
        'allowed-io': [],
        'max-line-length': 120
    })
