"""Backtest metrics, the projection API, and the dashboard callback."""

import numpy as np
import pytest

from election import config
from election.backtest import brier_score, load_inputs, log_loss, score
from election.projection import project, riding_table
from election.simulate import simulate


def test_brier_and_log_loss_on_known_values():
    probs = np.array([[1.0, 0.0], [0.5, 0.5]])
    winners = np.array([0, 1])
    assert brier_score(probs, winners) == pytest.approx((0.0 + 0.5) / 2)
    assert log_loss(probs, winners) == pytest.approx(-np.log(0.5) / 2)


def test_backtest_beats_naive_baseline():
    inputs = load_inputs()
    sim = simulate(inputs.base, inputs.forecast_regional(), n_trials=500, seed=1)
    m = score(sim, inputs)
    assert m["riding_accuracy"] > m["baseline_accuracy"]
    assert 0 <= m["brier"] <= 2
    assert sum(m["actual_seats"].values()) == config.TOTAL_SEATS


def test_backtest_uses_only_pre_election_information():
    inputs = load_inputs()
    forecast = inputs.forecast_regional()
    assert not np.allclose(forecast, inputs.actual.regional_shares(), atol=1e-3)


def test_projection_normalizes_inputs():
    shares = np.array([40, 40, 10, 5, 3, 1, 1], dtype=float)
    proj = project(shares, n_trials=200)
    assert proj.national.sum() == pytest.approx(1)
    assert (proj.sim.seats.sum(axis=1) == config.TOTAL_SEATS).all()


def test_projection_rejects_bad_input():
    with pytest.raises(ValueError):
        project(np.array([1.0, 2.0]))
    with pytest.raises(ValueError):
        project(-np.ones(len(config.PARTIES)))


def test_riding_table_shape():
    table = riding_table(project(n_trials=200))
    assert len(table) == config.TOTAL_SEATS
    assert table["win_prob"].between(0, 1).all()


def test_dashboard_callback_returns_all_outputs():
    from dashboard import compute

    bar, hist, region_map, rows, cards, note = compute([43, 40, 7, 6, 2, 1], "uniform")
    assert len(rows) == config.TOTAL_SEATS
    assert len(bar.data) == 1 and len(hist.data) == 2 and len(region_map.data) >= 1
    assert len(cards) == 2
    assert "99.0%" in note
