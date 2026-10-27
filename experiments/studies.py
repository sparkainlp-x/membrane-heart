"""One replicate of every study. Returns a flat {key: float} dict."""

import math
import random

from membrane_heart.core import TAU_STRATEGIES
from membrane_heart.probes import OOD_KINDS, GateScores
from membrane_heart.stats import mean, rng_for, roc_auc

from .common import (BASE_SIGMA, SIGMAS_A, SIGMAS_F_CAL, SIGMAS_F_EVAL,
                     accept_rate, build_heart, cal_probes, calibrated_heart,
                     eval_in, eval_ood, gate_taus, recognition, refuse_rate,
                     skey)

ABLATION_SIGMAS = (0.15, 0.30)

VARIANTS = {
    "default": {},
    "envelope_off": {"envelope": False},
    "width_2": {"width": 2.0},
    "width_4": {"width": 4.0},
    "width_6": {"width": 6.0},
    "width_12": {"width": 12.0},
    "width_16": {"width": 16.0},
    "width_24": {"width": 24.0},
    "width_64": {"width": 64.0},
    "phases_6": {"n_phases": 6},
    "phases_8": {"n_phases": 8},
    "n_32": {"n": 32},
    "n_128": {"n": 128},
    "n_32_snr": {"n": 32, "snr": True},
    "n_128_snr": {"n": 128, "snr": True},
    "k_2": {"k": 2},
    "k_3": {"k": 3},
    "k_6": {"k": 6},
    "k_8": {"k": 8},
    "pace_bottom": {"pacemaker_xy": (0.0, -16.0)},
    "pace_left_lobe": {"pacemaker_xy": (-10.0, 8.0)},
    "pace_centre": {"pacemaker_xy": (0.0, -2.0)},
}

# Out-of-library kinds that a calibrated gate is evaluated against.
KINDS = OOD_KINDS


def _variant_kwargs(spec, sigma):
    kw = {k: v for k, v in spec.items() if k != "snr"}
    eff = sigma
    if spec.get("snr"):
        eff = sigma * math.sqrt(64.0 / spec["n"])
    return kw, eff


def study_a(seed, ood_cache):
    out = {}
    for sigma in SIGMAS_A:
        heart, tau, j = calibrated_heart(seed, sigma)
        probes, labels = eval_in(heart, seed, sigma)
        ung, gat, _ = recognition(heart, probes, labels)
        p = f"A/s{skey(sigma)}"
        out[f"{p}/acc_ungated"] = ung
        out[f"{p}/acc_gated"] = gat
        out[f"{p}/accept_in"] = accept_rate(heart, probes)
        out[f"{p}/refuse_haar"] = refuse_rate(heart, ood_cache(heart, "haar"))
        out[f"{p}/refuse_phase_scramble"] = refuse_rate(
            heart, ood_cache(heart, "phase_scramble"))
        out[f"{p}/tau"] = tau
        out[f"{p}/j_cal"] = j
    return out


def study_b(seed):
    out = {}
    for sigma in ABLATION_SIGMAS:
        base = None
        for name, spec in VARIANTS.items():
            kw, eff = _variant_kwargs(spec, sigma)
            heart, tau, j = calibrated_heart(seed, eff, **kw)
            probes, labels = eval_in(heart, seed, eff)
            ung, gat, _ = recognition(heart, probes, labels)
            p = f"B/s{skey(sigma)}/{name}"
            out[f"{p}/acc_ungated"] = ung
            out[f"{p}/acc_gated"] = gat
            out[f"{p}/j_cal"] = j
            out[f"{p}/max_nbr_overlap"] = heart.max_neighbour_overlap()
            if name == "default":
                base = (ung, gat)
            else:
                out[f"{p}/diff_acc_ungated"] = ung - base[0]
                out[f"{p}/diff_acc_gated"] = gat - base[1]
    return out


def study_c(seed, base, ood_cache):
    """Gate comparison and tau-rule comparison at the base sigma."""
    out = {}
    heart, cal_in, cal_ood = base["heart"], base["cal_in"], base["cal_ood"]
    gs = GateScores(heart, scan_points=40)
    taus = gate_taus(heart, cal_in, cal_ood, gs)
    in_probes, _ = eval_in(heart, seed, BASE_SIGMA)
    in_scores = {g: [gs.score(g, f) for f in in_probes]
                 for g in taus}
    accept_in = {g: sum(s >= taus[g][0] for s in in_scores[g])
                 / len(in_probes) for g in taus}
    for g in taus:
        out[f"C/{g}/tau"] = taus[g][0]
        out[f"C/{g}/j_cal"] = taus[g][1]
        out[f"C/{g}/accept_in"] = accept_in[g]
    for kind in KINDS:
        ood = ood_cache(heart, kind)
        auc, bal = {}, {}
        for g in taus:
            sc = [gs.score(g, f) for f in ood]
            auc[g] = roc_auc(in_scores[g], sc)
            refuse = sum(v < taus[g][0] for v in sc) / len(sc)
            bal[g] = (accept_in[g] + refuse) / 2.0
            out[f"C/{g}/auc_{kind}"] = auc[g]
            out[f"C/{g}/bal_{kind}"] = bal[g]
        out[f"C/diff_auc_max_overlap_minus_wave_scan/{kind}"] = (
            auc["max_overlap"] - auc["wave_scan"])
        out[f"C/diff_auc_max_overlap_minus_magnitude_profile/{kind}"] = (
            auc["max_overlap"] - auc["magnitude_profile"])
        out[f"C/diff_bal_max_overlap_minus_wave_scan/{kind}"] = (
            bal["max_overlap"] - bal["wave_scan"])
        out[f"C/diff_bal_max_overlap_minus_magnitude_profile/{kind}"] = (
            bal["max_overlap"] - bal["magnitude_profile"])
    # tau rules, held-out balanced accuracy vs Haar and vs phase scramble
    rule = {}
    for strat in TAU_STRATEGIES:
        h2, tau, j = calibrated_heart(seed, BASE_SIGMA, strategy=strat)
        acc = accept_rate(h2, in_probes)
        for kind in ("haar", "phase_scramble"):
            ref = refuse_rate(h2, ood_cache(h2, kind))
            rule[(strat, kind)] = (acc + ref) / 2.0
            out[f"C/rule/{strat}/bal_{kind}"] = rule[(strat, kind)]
        out[f"C/rule/{strat}/tau"] = tau
        out[f"C/rule/{strat}/accept_in"] = acc
    for strat in TAU_STRATEGIES:
        if strat == "midpoint":
            continue
        for kind in ("haar", "phase_scramble"):
            out[f"C/rule/diff_bal_{kind}/midpoint_minus_{strat}"] = (
                rule[("midpoint", kind)] - rule[(strat, kind)])
    # Noise-matched control: out-of-library probes get the same noise
    # as the in-library probes (exploratory; see PROTOCOL amendment A1).
    for kind in KINDS:
        ood = ood_cache(heart, kind, BASE_SIGMA)
        auc, bal = {}, {}
        for g in taus:
            sc = [gs.score(g, f) for f in ood]
            auc[g] = roc_auc(in_scores[g], sc)
            refuse = sum(v < taus[g][0] for v in sc) / len(sc)
            bal[g] = (accept_in[g] + refuse) / 2.0
            out[f"Cn/{g}/auc_{kind}"] = auc[g]
            out[f"Cn/{g}/bal_{kind}"] = bal[g]
        out[f"Cn/diff_auc_max_overlap_minus_wave_scan/{kind}"] = (
            auc["max_overlap"] - auc["wave_scan"])
        out[f"Cn/diff_auc_max_overlap_minus_magnitude_profile/{kind}"] = (
            auc["max_overlap"] - auc["magnitude_profile"])
    return out


def study_d(seed, base, ood_cache):
    out = {}
    heart = base["heart"]
    probes, labels = eval_in(heart, seed, BASE_SIGMA)
    rng = rng_for("shuffle", seed)
    shuffled = list(labels)
    rng.shuffle(shuffled)
    preds = [heart.project(f)[0] for f in probes]
    out["D/shuffled/acc_ungated"] = sum(
        p == s for p, s in zip(preds, shuffled)) / len(probes)
    out["D/shuffled/chance"] = 1.0 / heart.n_phases
    out["D/accept_in"] = accept_rate(heart, probes)
    for kind in KINDS:
        ood = ood_cache(heart, kind)
        out[f"D/refuse_{kind}"] = refuse_rate(heart, ood)
        out[f"D/max_overlap_{kind}"] = mean(
            heart.max_overlap(f) for f in ood)
    out["D/max_overlap_in"] = mean(heart.max_overlap(f) for f in probes)
    for kind in KINDS:
        ood = ood_cache(heart, kind, BASE_SIGMA)
        out[f"D/noisy/refuse_{kind}"] = refuse_rate(heart, ood)
        out[f"D/noisy/max_overlap_{kind}"] = mean(
            heart.max_overlap(f) for f in ood)
    return out


def study_e(seed, ood_cache):
    out = {}
    for sigma in (0.0, 0.05, 0.15):
        heart, tau, j = calibrated_heart(seed, sigma, envelope=False)
        probes, labels = eval_in(heart, seed, sigma)
        ung, gat, idx0 = recognition(heart, probes, labels)
        p = f"E/s{skey(sigma)}"
        out[f"{p}/acc_ungated"] = ung
        out[f"{p}/acc_gated"] = gat
        out[f"{p}/frac_index0"] = idx0
        out[f"{p}/j_cal"] = j
        out[f"{p}/refuse_haar"] = refuse_rate(heart,
                                              ood_cache(heart, "haar"))
        out[f"{p}/max_nbr_overlap"] = heart.max_neighbour_overlap()
    return out


def study_f(seed, ood_cache):
    out = {}
    for sc in SIGMAS_F_CAL:
        heart, tau, j = calibrated_heart(seed, sc)
        p = f"F/c{skey(sc)}"
        out[f"{p}/tau"] = tau
        out[f"{p}/j_cal"] = j
        out[f"{p}/refuse_haar"] = refuse_rate(heart, ood_cache(heart, "haar"))
        out[f"{p}/refuse_phase_scramble"] = refuse_rate(
            heart, ood_cache(heart, "phase_scramble"))
        for se in SIGMAS_F_EVAL:
            probes, _ = eval_in(heart, seed, se)
            out[f"{p}/e{skey(se)}/accept_in"] = accept_rate(heart, probes)
    return out


def study_g(seed):
    """Does the phase structure matter? Magnitude-only recognition."""
    out = {}
    for sigma in SIGMAS_A:
        heart = build_heart(seed)
        gs = GateScores(heart, scan_points=4)
        probes, labels = eval_in(heart, seed, sigma)
        mag = sum(gs.classify_magnitude_only(f) == lab
                  for f, lab in zip(probes, labels)) / len(probes)
        ung, _, _ = recognition(heart, probes, labels)
        p = f"G/s{skey(sigma)}"
        out[f"{p}/acc_magnitude_only"] = mag
        out[f"{p}/acc_complex"] = ung
        out[f"{p}/diff_complex_minus_magnitude_only"] = ung - mag
    return out


def replicate(seed):
    """All studies for one seed. Pure function of the seed."""
    base_heart, base_tau, base_j = calibrated_heart(seed, BASE_SIGMA)
    cal_in, cal_ood = cal_probes(base_heart, seed, BASE_SIGMA)
    base = {"heart": base_heart, "cal_in": cal_in, "cal_ood": cal_ood}
    cache = {}

    def ood_cache(heart, kind, sigma=0.0):
        # Out-of-library eval sets depend only on the layout (seed),
        # the kind and the matched-noise level, so every study at the
        # same n and phase count reuses one set per kind.
        key = (heart.n, heart.n_phases, kind, sigma)
        if key not in cache:
            cache[key] = eval_ood(heart, seed, kind, sigma)
        return cache[key]

    out = {}
    out.update(study_a(seed, ood_cache))
    out.update(study_b(seed))
    out.update(study_c(seed, base, ood_cache))
    out.update(study_d(seed, base, ood_cache))
    out.update(study_e(seed, ood_cache))
    out.update(study_f(seed, ood_cache))
    out.update(study_g(seed))
    return out
