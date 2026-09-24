"""Properties the swing model and simulation must satisfy."""

import numpy as np
import pandas as pd
import pytest

from election import config
from election.data import ElectionResult, load_results
from election.simulate import NoiseModel, simulate
from election.swing import SWING_METHODS, apply_swing, national_to_regional

NO_NOISE = NoiseModel(0.0, 0.0, 0.0)


@pytest.fixture(scope="module")
def base():
    return load_results(config.RESULTS_2025)


def _toy_result(votes: list[list[float]]) -> ElectionResult:
    """Ontario-only toy election with one row per riding."""
    n = len(votes)
    ridings = pd.DataFrame(
        {"riding_name": [f"R{i}" for i in range(n)], "province": ["ON"] * n, "region": ["ON"] * n},
        index=pd.Index(range(n), name="riding_id"),
    )
    full = np.zeros((n, len(config.PARTIES)))
    full[:, : len(votes[0])] = votes
    return ElectionResult(ridings=ridings, votes=full)


@pytest.mark.parametrize("method", SWING_METHODS)
def test_no_change_in_polls_means_no_change_in_ridings(base, method):
    reg = base.regional_shares()[base.region_index]
    out = apply_swing(base.shares, reg, reg, method)
    assert np.allclose(out, base.shares)


@pytest.mark.parametrize("method", SWING_METHODS)
def test_swing_output_is_a_valid_distribution(base, method):
    target = base.regional_shares().copy()
    target[:, 0] += 0.10  # big Liberal gain everywhere
    target /= target.sum(axis=1, keepdims=True)
    out = apply_swing(base.shares, base.regional_shares()[base.region_index], target[base.region_index], method)
    assert (out >= 0).all()
    assert np.allclose(out.sum(axis=1), 1)


def test_party_absent_in_baseline_stays_absent(base):
    bq = config.PARTIES.index("BQ")
    target = base.regional_shares().copy()
    target[:, bq] = 0.3  # nonsense poll putting the Bloc at 30% everywhere
    target /= target.sum(axis=1, keepdims=True)
    out = apply_swing(base.shares, base.regional_shares()[base.region_index], target[base.region_index])
    outside_qc = base.ridings["province"].to_numpy() != "QC"
    assert (out[outside_qc, bq] == 0).all()


def test_proportional_swing_scales_by_ratio():
    base = np.array([[0.2, 0.8], [0.4, 0.6]])
    base_reg = np.array([[0.3, 0.7], [0.3, 0.7]])
    target = np.array([[0.6, 0.4], [0.6, 0.4]])  # party 0 doubles
    out = apply_swing(base, base_reg, target, "proportional")
    raw0 = np.array([0.4, 0.8])
    raw1 = np.array([0.8 * 4 / 7, 0.6 * 4 / 7])
    assert np.allclose(out[:, 0], raw0 / (raw0 + raw1))


def test_national_to_regional_preserves_national_total(base):
    target = base.national_shares().copy()
    target[0] += 0.05
    target[1] -= 0.05
    reg = national_to_regional(target, base.national_shares(), base.regional_shares(), base.region_weights())
    implied_national = (reg * base.region_weights()[:, None]).sum(axis=0)
    assert np.allclose(implied_national, target, atol=1e-3)


def test_bloc_national_change_is_concentrated_in_quebec(base):
    bq, qc = config.PARTIES.index("BQ"), config.REGIONS.index("QC")
    target = base.national_shares().copy()
    target[bq] += 0.01
    target /= target.sum()
    reg = national_to_regional(target, base.national_shares(), base.regional_shares(), base.region_weights())
    gain_qc = reg[qc, bq] - base.regional_shares()[qc, bq]
    assert gain_qc > 0.03  # Quebec casts ~23% of votes, so +1 national is ~+4 in Quebec
    assert np.allclose(np.delete(reg[:, bq], qc), 0)


def test_first_past_the_post_winner_takes_the_seat():
    # A 40/35/25 split wins every riding under FPTP, not 40% of them.
    toy = _toy_result([[40, 35, 25]] * 10)
    sim = simulate(toy, toy.regional_shares(), n_trials=50, noise=NO_NOISE)
    assert (sim.seats[:, 0] == 10).all()


def test_seats_sum_to_total(base):
    sim = simulate(base, base.regional_shares(), n_trials=200)
    assert (sim.seats.sum(axis=1) == config.TOTAL_SEATS).all()
    assert np.allclose(sim.win_prob.sum(axis=1), 1)


def test_zero_noise_reproduces_baseline_winners(base):
    sim = simulate(base, base.regional_shares(), n_trials=20, noise=NO_NOISE)
    assert (sim.point_winners() == base.winners()).all()
    assert (sim.seats == sim.seats[0]).all()
    assert sim.point_seats() == base.seat_counts()


def test_seed_makes_runs_reproducible(base):
    a = simulate(base, base.regional_shares(), n_trials=300, seed=7)
    b = simulate(base, base.regional_shares(), n_trials=300, seed=7)
    assert (a.seats == b.seats).all()


def test_more_noise_means_wider_seat_distribution(base):
    narrow = simulate(base, base.regional_shares(), n_trials=2000, noise=NoiseModel().scaled(0.5))
    wide = simulate(base, base.regional_shares(), n_trials=2000, noise=NoiseModel().scaled(2.0))
    lpc = config.PARTIES.index("LPC")
    assert wide.seats[:, lpc].std() > narrow.seats[:, lpc].std()


def test_small_chunks_still_produce_valid_results(base):
    sim = simulate(base, base.regional_shares(), n_trials=500, seed=3, chunk_size=128)
    assert sim.seats.shape == (500, len(config.PARTIES))
    assert (sim.seats.sum(axis=1) == config.TOTAL_SEATS).all()
