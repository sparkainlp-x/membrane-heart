"""Shared helpers: seed sets, probe streams, gate calibration."""

import math

from membrane_heart import MembraneHeart, noisy, rand_field
from membrane_heart.core import calibrate_tau
from membrane_heart.probes import OOD_KINDS, GateScores, make_ood
from membrane_heart.stats import rng_for

SEED_SETS = {
    "dev": list(range(1000, 1200)),
    "confirm": list(range(5000, 5200)),
    "smoke": list(range(9001, 9006)),
}

N_CAL_IN = 100
N_CAL_OOD = 100
N_EVAL_IN = 100
N_EVAL_OOD = 50

SIGMAS_A = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.45, 0.60)
SIGMAS_F_CAL = (0.05, 0.15, 0.30)
SIGMAS_F_EVAL = (0.0, 0.05, 0.15, 0.30, 0.45, 0.60)
BASE_SIGMA = 0.15


def skey(x):
    """Stable string for a sigma value in result keys."""
    return f"{x:.2f}"


def build_heart(seed, **kw):
    return MembraneHeart(seed=seed, **kw)


def cal_probes(heart, seed, sigma):
    """Calibration probes: in-library (cycling phases) + Haar fields."""
    rng = rng_for("cal", seed, skey(sigma))
    ins = [noisy(heart.patterns[k % heart.n_phases], sigma, rng)
           for k in range(N_CAL_IN)]
    ood = [rand_field(heart.n, rng) for _ in range(N_CAL_OOD)]
    return ins, ood


def eval_in(heart, seed, sigma):
    """Held-out in-library probes with their true labels."""
    rng = rng_for("eval", seed, "in", skey(sigma))
    probes, labels = [], []
    for k in range(N_EVAL_IN):
        i = k % heart.n_phases
        probes.append(noisy(heart.patterns[i], sigma, rng))
        labels.append(i)
    return probes, labels


def eval_ood(heart, seed, kind, sigma=0.0):
    """Held-out out-of-library probes of one kind.

    ``sigma > 0`` adds the same absolute complex Gaussian noise that
    in-library probes carry (a noise-matched control); the sigma = 0
    stream is unchanged so earlier numbers stay reproducible.
    """
    if sigma > 0:
        rng = rng_for("eval", seed, "ood", kind, skey(sigma))
    else:
        rng = rng_for("eval", seed, "ood", kind)
    out = []
    for _ in range(N_EVAL_OOD):
        f = make_ood(heart, kind, rng)
        out.append(noisy(f, sigma, rng) if sigma > 0 else f)
    return out


def calibrated_heart(seed, sigma, strategy="midpoint", **kw):
    heart = build_heart(seed, **kw)
    ins, ood = cal_probes(heart, seed, sigma)
    tau, j = heart.calibrate(ins, ood, strategy=strategy)
    return heart, tau, j


def accept_rate(heart, probes):
    return sum(heart.decide(f)[0] == "accept" for f in probes) / len(probes)


def refuse_rate(heart, probes):
    return 1.0 - accept_rate(heart, probes)


def recognition(heart, probes, labels):
    """(ungated accuracy, gated accuracy, fraction predicted index 0)."""
    ung = gat = idx0 = 0
    for f, lab in zip(probes, labels):
        winner, _ = heart.project(f)
        ung += winner == lab
        idx0 += winner == 0
        verdict, name, _ = heart.decide(f)
        gat += verdict == "accept" and name == heart.phase_names[lab]
    n = len(probes)
    return ung / n, gat / n, idx0 / n


def gate_taus(heart, cal_in, cal_ood, gs, grid=101):
    """tau and J for each non-trivial gate from one calibration set."""
    out = {}
    for name in ("max_overlap", "wave_scan", "magnitude_profile"):
        a = [gs.score(name, f) for f in cal_in]
        b = [gs.score(name, f) for f in cal_ood]
        out[name] = calibrate_tau(a, b, grid)
    return out


def is_finite(x):
    return isinstance(x, float) and math.isfinite(x)


__all__ = [n for n in dir() if not n.startswith("_")]
