"""The processed data must reproduce official Elections Canada figures."""

import numpy as np
import pandas as pd
import pytest

from election import config
from election.data import load_polls, load_results, poll_average


@pytest.fixture(scope="module")
def r2021():
    return load_results(config.RESULTS_2021)


@pytest.fixture(scope="module")
def r2025():
    return load_results(config.RESULTS_2025)


def test_riding_counts(r2021, r2025):
    assert len(r2021.ridings) == len(r2025.ridings) == 343
    assert (r2021.ridings.index == r2025.ridings.index).all()


def test_2025_official_seat_totals(r2025):
    assert r2025.seat_counts() == {"LPC": 169, "CPC": 144, "NDP": 7, "BQ": 22, "GPC": 1, "PPC": 0, "OTH": 0}


def test_2025_official_national_shares(r2025):
    nat = dict(zip(config.PARTIES, r2025.national_shares() * 100, strict=True))
    assert nat["LPC"] == pytest.approx(43.76, abs=0.02)
    assert nat["CPC"] == pytest.approx(41.31, abs=0.02)
    assert nat["BQ"] == pytest.approx(6.29, abs=0.02)


def test_2021_official_national_shares(r2021):
    nat = dict(zip(config.PARTIES, r2021.national_shares() * 100, strict=True))
    assert nat["LPC"] == pytest.approx(32.62, abs=0.02)
    assert nat["CPC"] == pytest.approx(33.74, abs=0.02)
    assert nat["NDP"] == pytest.approx(17.83, abs=0.02)


def test_2021_transposed_matches_elections_canada_spot_checks(r2021):
    """Values copied from Elections Canada's transposition_343_fed.csv."""
    idx = {rid: i for i, rid in enumerate(r2021.ridings.index)}
    checks = {
        (10002, "LPC"): 19467,
        (10002, "NDP"): 8227,  # Cape Spear
        (12006, "NDP"): 19160,
        (12006, "LPC"): 20087,  # Halifax
        (24006, "CPC"): 27514,
        (24006, "PPC"): 10362,  # Beauce
    }
    for (rid, party), votes in checks.items():
        assert r2021.votes[idx[rid], config.PARTIES.index(party)] == votes


def test_bloc_only_in_quebec(r2021, r2025):
    bq = config.PARTIES.index("BQ")
    for res in (r2021, r2025):
        outside = res.ridings["province"].to_numpy() != "QC"
        assert res.votes[outside, bq].sum() == 0


def test_shares_are_valid(r2025):
    assert np.allclose(r2025.shares.sum(axis=1), 1)
    assert np.allclose(r2025.regional_shares().sum(axis=1), 1)
    assert r2025.region_weights().sum() == pytest.approx(1)


def test_poll_average_uses_latest_poll_per_firm():
    polls = pd.DataFrame(
        {
            "pollster": ["A", "A", "B"],
            "end_date": pd.to_datetime(["2025-01-01", "2025-01-05", "2025-01-03"]),
            "region": ["NAT"] * 3,
            **{p: [0.0] * 3 for p in config.PARTIES},
        }
    )
    polls.loc[0, "LPC"], polls.loc[0, "CPC"] = 90, 10  # old poll from A: must be ignored
    polls.loc[1, "LPC"], polls.loc[1, "CPC"] = 50, 50
    polls.loc[2, "LPC"], polls.loc[2, "CPC"] = 30, 70
    avg = dict(zip(config.PARTIES, poll_average(polls), strict=True))
    assert avg["LPC"] == pytest.approx(0.40)
    assert avg["CPC"] == pytest.approx(0.60)


def test_poll_files_load():
    for path in (config.POLLS_2025_FINAL_WEEK, config.POLLS_LATEST):
        avg = poll_average(load_polls(path))
        assert avg.sum() == pytest.approx(1)
        assert (avg >= 0).all()
