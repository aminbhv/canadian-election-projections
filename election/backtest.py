"""Backtest: forecast the 2025 election using only information available beforehand.

Inputs:  2021 results transposed onto the 2025 riding map + final-week 2025 national polls.
Target:  actual 2025 riding results.

Two scenarios separate the two sources of error:

* forecast: regional shares come from national polls (uniform national swing).
  This is a genuine out-of-sample forecast.
* oracle:   regional shares are the *actual* 2025 regional results. Any error
  left over comes from the swing model itself, not from the polls.

Run:  python -m election.backtest
"""

import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

from election import config
from election.data import ElectionResult, load_polls, load_results, poll_average
from election.simulate import NoiseModel, SimulationResult, simulate
from election.swing import SWING_METHODS, national_to_regional

N_TRIALS = 10_000
SEED = 2025


@dataclass(frozen=True)
class BacktestInputs:
    base: ElectionResult  # 2021 transposed
    actual: ElectionResult  # 2025
    national_polls: np.ndarray  # final-week average, shape (P,)

    def forecast_regional(self) -> np.ndarray:
        return national_to_regional(
            self.national_polls,
            self.base.national_shares(),
            self.base.regional_shares(),
            self.base.region_weights(),
        )

    def oracle_regional(self) -> np.ndarray:
        return self.actual.regional_shares()


def load_inputs() -> BacktestInputs:
    return BacktestInputs(
        base=load_results(config.RESULTS_2021),
        actual=load_results(config.RESULTS_2025),
        national_polls=poll_average(load_polls(config.POLLS_2025_FINAL_WEEK)),
    )


def brier_score(win_prob: np.ndarray, actual_winners: np.ndarray) -> float:
    """Multi-class Brier score averaged over ridings (0 is perfect, lower is better)."""
    onehot = np.eye(win_prob.shape[1])[actual_winners]
    return float(((win_prob - onehot) ** 2).sum(axis=1).mean())


def log_loss(win_prob: np.ndarray, actual_winners: np.ndarray, floor: float = 1e-3) -> float:
    p = np.clip(win_prob[np.arange(len(actual_winners)), actual_winners], floor, 1.0)
    return float(-np.log(p).mean())


def calibration_table(win_prob: np.ndarray, actual_winners: np.ndarray) -> pd.DataFrame:
    """For the projected favourite in each riding: stated confidence vs how often it won."""
    fav = win_prob.argmax(axis=1)
    conf = win_prob.max(axis=1)
    hit = fav == actual_winners
    bins = [0.0, 0.6, 0.7, 0.8, 0.9, 0.99, 1.0001]
    labels = ["<60%", "60-70%", "70-80%", "80-90%", "90-99%", "99%+"]
    df = pd.DataFrame({"bin": pd.cut(conf, bins, labels=labels, right=False), "conf": conf, "hit": hit})
    out = df.groupby("bin", observed=False).agg(
        ridings=("hit", "size"), mean_confidence=("conf", "mean"), actual_hit_rate=("hit", "mean")
    )
    return out


def score(result: SimulationResult, inputs: BacktestInputs) -> dict:
    actual_w = inputs.actual.winners()
    base_w = inputs.base.winners()
    point_w = result.point_winners()
    actual_seats = inputs.actual.seat_counts()
    mean_seats = dict(zip(config.PARTIES, result.seats.mean(axis=0), strict=True))

    changed = actual_w != base_w
    lpc, cpc = config.PARTIES.index("LPC"), config.PARTIES.index("CPC")
    return {
        "riding_accuracy": float((point_w == actual_w).mean()),
        "baseline_accuracy": float((base_w == actual_w).mean()),
        "ridings_changed_hands": int(changed.sum()),
        "changed_hands_called": int((point_w[changed] == actual_w[changed]).sum()),
        "brier": brier_score(result.win_prob, actual_w),
        "log_loss": log_loss(result.win_prob, actual_w),
        "point_seats": result.point_seats(),
        "mean_seats": {p: round(float(v), 1) for p, v in mean_seats.items()},
        "actual_seats": actual_seats,
        "seat_mae": float(np.mean([abs(mean_seats[p] - actual_seats[p]) for p in config.PARTIES])),
        "p_lpc_majority": float((result.seats[:, lpc] >= config.MAJORITY_THRESHOLD).mean()),
        "p_lpc_most_seats": float(result.summary().loc["LPC", "p_most_seats"]),
        # Where the real result fell in the simulated distribution (0.5 = dead centre).
        "lpc_actual_percentile": float((result.seats[:, lpc] < actual_seats["LPC"]).mean()),
        "cpc_actual_percentile": float((result.seats[:, cpc] < actual_seats["CPC"]).mean()),
    }


def regional_seat_errors(result: SimulationResult, inputs: BacktestInputs) -> pd.DataFrame:
    """Projected minus actual seats, by region and party (point projection)."""
    region = inputs.actual.ridings["region"].to_numpy()
    rows = []
    for g in config.REGIONS:
        mask = region == g
        proj = np.bincount(result.point_winners()[mask], minlength=len(config.PARTIES))
        act = np.bincount(inputs.actual.winners()[mask], minlength=len(config.PARTIES))
        rows.append(
            {"region": config.REGION_NAMES[g], **{p: int(d) for p, d in zip(config.PARTIES, proj - act, strict=True)}}
        )
    return pd.DataFrame(rows).set_index("region")[["LPC", "CPC", "NDP", "BQ", "GPC"]]


def run(n_trials: int = N_TRIALS, seed: int = SEED) -> dict:
    inputs = load_inputs()
    scenarios = {"forecast": inputs.forecast_regional(), "oracle": inputs.oracle_regional()}

    results = {}
    for name, regional in scenarios.items():
        for method in SWING_METHODS:
            sim = simulate(inputs.base, regional, n_trials, method=method, seed=seed)
            results[f"{name}/{method}"] = {"sim": sim, "metrics": score(sim, inputs)}

    sensitivity = []
    for factor in (0.5, 1.0, 1.5, 2.0, 3.0):
        sim = simulate(inputs.base, scenarios["forecast"], n_trials, noise=NoiseModel().scaled(factor), seed=seed)
        m = score(sim, inputs)
        sensitivity.append(
            {
                "noise_factor": factor,
                "brier": m["brier"],
                "log_loss": m["log_loss"],
                "p_lpc_majority": m["p_lpc_majority"],
                "lpc_actual_percentile": m["lpc_actual_percentile"],
            }
        )

    default = results["forecast/proportional"]
    return {
        "inputs": inputs,
        "results": results,
        "sensitivity": pd.DataFrame(sensitivity),
        "calibration": calibration_table(default["sim"].win_prob, inputs.actual.winners()),
        "regional_errors_forecast": regional_seat_errors(default["sim"], inputs),
        "regional_errors_oracle": regional_seat_errors(results["oracle/proportional"]["sim"], inputs),
    }


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def to_markdown(report: dict) -> str:
    inputs: BacktestInputs = report["inputs"]
    polls = dict(zip(config.PARTIES, inputs.national_polls, strict=True))
    actual_nat = dict(zip(config.PARTIES, inputs.actual.national_shares(), strict=True))
    lines = [
        "# Backtest: 2025 Canadian federal election",
        "",
        "Generated by `python -m election.backtest`. Baseline: 2021 results transposed to the",
        f"343-riding map. {N_TRIALS:,} trials per run, seed {SEED}.",
        "",
        "## Polling input vs actual national result",
        "",
        "| Party | Final-week poll average | Actual |",
        "|---|---|---|",
    ]
    for p in ("LPC", "CPC", "NDP", "BQ", "GPC", "PPC"):
        lines.append(f"| {p} | {_pct(polls[p])} | {_pct(actual_nat[p])} |")

    lines += [
        "",
        "## Headline results",
        "",
        "| Scenario / swing | Ridings correct | Changed-hands ridings called | Brier | Seat MAE | P(LPC majority) |",
        "|---|---|---|---|---|---|",
    ]
    for key, r in report["results"].items():
        m = r["metrics"]
        lines.append(
            f"| {key} | {_pct(m['riding_accuracy'])} | {m['changed_hands_called']}/{m['ridings_changed_hands']} "
            f"| {m['brier']:.3f} | {m['seat_mae']:.1f} | {_pct(m['p_lpc_majority'])} |"
        )
    base_acc = next(iter(report["results"].values()))["metrics"]["baseline_accuracy"]
    lines += [
        "",
        f"Naive baseline (every riding re-elects its 2021 winner): {_pct(base_acc)} of ridings correct,",
        "0 changed-hands ridings called.",
        "",
        "## Seats: projected vs actual (forecast / proportional swing)",
        "",
        "| Party | Point projection | Simulation mean | Actual |",
        "|---|---|---|---|",
    ]
    m = report["results"]["forecast/proportional"]["metrics"]
    for p in ("LPC", "CPC", "BQ", "NDP", "GPC"):
        lines.append(f"| {p} | {m['point_seats'][p]} | {m['mean_seats'][p]} | {m['actual_seats'][p]} |")
    lines += [
        "",
        f"The actual Liberal seat total fell at the {_pct(m['lpc_actual_percentile'])} percentile of the",
        f"simulated distribution, and the Conservative total at the {_pct(m['cpc_actual_percentile'])} percentile.",
        "",
        "## Where the seat errors came from (projected minus actual)",
        "",
        "Forecast (national polls):",
        "",
        report["regional_errors_forecast"].to_markdown(),
        "",
        "Oracle (actual regional vote shares, so this is swing-model error only):",
        "",
        report["regional_errors_oracle"].to_markdown(),
        "",
        "## Calibration (forecast / proportional swing)",
        "",
        "For each riding's projected favourite: how confident the model was vs how often it won.",
        "",
        report["calibration"].to_markdown(floatfmt=("", ".0f", ".2f", ".2f")),
        "",
        "## Noise sensitivity (forecast / proportional swing)",
        "",
        "Multiplying all three error layers by a factor. Factor 1.0 is the default, which was",
        "fixed before running this backtest. This table is diagnostic only; tuning on it would",
        "overfit to a single election.",
        "",
        report["sensitivity"].to_markdown(index=False, floatfmt=".3f"),
        "",
    ]
    return "\n".join(lines)


def to_json(report: dict) -> dict:
    return {
        "results": {k: v["metrics"] for k, v in report["results"].items()},
        "sensitivity": report["sensitivity"].to_dict(orient="records"),
    }


def main() -> None:
    report = run()
    config.REPORTS_DIR.mkdir(exist_ok=True)
    md = to_markdown(report)
    (config.REPORTS_DIR / "backtest_2025.md").write_text(md, encoding="utf-8")
    (config.REPORTS_DIR / "backtest_2025.json").write_text(json.dumps(to_json(report), indent=2), encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
