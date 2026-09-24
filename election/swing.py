"""Swing models: turn a change in regional vote share into riding-level shares.

A swing model answers: "if a party goes from 30% to 36% in Ontario, what
happens in each Ontario riding?" Two classic answers:

* uniform swing: every riding moves by the same number of points (+6).
* proportional swing: every riding is scaled by the same ratio (x1.2).
  CBC's Poll Tracker uses proportional swing.

Uniform swing overstates change for small parties in their weak ridings;
proportional swing overstates change in a party's strongholds. "hybrid"
averages the two.
"""

import numpy as np

SWING_METHODS = ("proportional", "uniform", "hybrid")
_EPS = 1e-9


def _normalize(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, None)
    return x / x.sum(axis=-1, keepdims=True)


def apply_swing(
    base: np.ndarray,
    base_regional: np.ndarray,
    target_regional: np.ndarray,
    method: str = "proportional",
) -> np.ndarray:
    """Project riding shares given each riding's regional baseline and target.

    Args:
        base: riding shares in the baseline election, shape (R, P).
        base_regional: baseline share of each riding's region, shape (R, P).
        target_regional: projected share of each riding's region, shape (R, P)
            or (T, R, P) for T simulation trials.
        method: one of SWING_METHODS.

    Returns:
        Projected riding shares with the shape of target_regional; rows sum to 1.
    """
    if method not in SWING_METHODS:
        raise ValueError(f"unknown swing method {method!r}; choose from {SWING_METHODS}")

    uniform = base + (target_regional - base_regional)

    # Ratio is undefined where a party had no regional vote in the baseline;
    # fall back to uniform swing there.
    safe = base_regional > _EPS
    ratio = np.where(safe, target_regional / np.where(safe, base_regional, 1.0), 0.0)
    proportional = np.where(safe, base * ratio, uniform)

    if method == "uniform":
        projected = uniform
    elif method == "proportional":
        projected = proportional
    else:
        projected = 0.5 * (np.clip(uniform, 0, None) + np.clip(proportional, 0, None))

    # A party that did not run in a riding in the baseline stays at zero there.
    projected = np.where(base > 0, projected, 0.0)
    return _normalize(projected)


def national_to_regional(
    national_target: np.ndarray,
    national_base: np.ndarray,
    regional_base: np.ndarray,
    region_weights: np.ndarray,
) -> np.ndarray:
    """Spread a national poll across regions using uniform national swing.

    Each party's change in national share is added to every region where it
    ran. A party that only runs in some regions (the Bloc runs only in Quebec)
    has its national change concentrated there: a 1-point national Bloc gain
    is roughly a 4-point gain in Quebec, which casts about a quarter of votes.

    Args:
        national_target: projected national shares, shape (P,).
        national_base: baseline national shares, shape (P,).
        regional_base: baseline regional shares, shape (G, P).
        region_weights: each region's fraction of national votes, shape (G,).

    Returns:
        Projected regional shares, shape (G, P); rows sum to 1.
    """
    present = regional_base > 1e-4
    weight_present = (region_weights[:, None] * present).sum(axis=0)
    delta = (national_target - national_base) / np.where(weight_present > 0, weight_present, 1.0)
    projected = regional_base + delta[None, :] * present
    return _normalize(projected)
