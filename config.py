"""
Canadian Election Simulator - Configuration Module
Copyright (c) 2025 [Your Name]

This module contains configuration constants used throughout the application.
"""

# Provincial seat distribution
SEATS_BY_PROVINCE = {
    "British Columbia": 43,
    "Alberta": 37,
    "Sask. & Man.": 28,
    "Ontario": 122,
    "Quebec": 78,
    "Atlantic Canada": 32,
}

# Parliament majority threshold
MAJORITY_THRESHOLD = 172

# Party color scheme for visualization
PARTY_COLORS = {
    "LIB": "red",
    "CON": "blue",
    "NDP": "orange",
    "GRN": "green",
    "BQ": "deepskyblue",
    "PPC": "purple",
    "OTH": "grey"
}

# Valid parties for data cleaning
VALID_PARTIES = {"LIB", "CON", "NDP", "GRN", "BQ", "PPC"}

# Province mapping for data cleaning
PROVINCE_MAP = {
    "British Columbia": "British Columbia",
    "Alberta": "Alberta",
    "Sask. & Man.": ["Saskatchewan", "Manitoba"],
    "Ontario": "Ontario",
    "Quebec": "Quebec",
    "Atlantic Canada": ["Newfoundland and Labrador", "Prince Edward Island", "Nova Scotia", "New Brunswick"]
}


if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'extra-imports': [],  # Add any additional imports here
        'allowed-io': [],     # List functions that perform input/output
        'max-line-length': 120
    })
