"""Run every study over a seed set and write a JSON summary.

    python -m experiments.run_all --set dev --out docs/results/dev.json
    python -m experiments.run_all --set confirm --out docs/results/confirm.json

Outputs are deterministic given the code and the seed set (floating
point rounding aside; values are rounded to 6 decimals).
"""

import argparse
import json
import multiprocessing
import platform
import sys

from membrane_heart import __version__
from membrane_heart.stats import (bootstrap_ci, bootstrap_p, holm, rng_for,
                                  wilson_interval)

from .common import SEED_SETS, N_EVAL_IN, N_EVAL_OOD
from .studies import replicate

# (id, key, null, alternative, statement)
HYPOTHESES = [
    ("H1", "A/s0.15/acc_ungated", 0.90, "greater",
     "recognition accuracy at sigma 0.15 exceeds 0.90"),
    ("H2", "A/s0.15/refuse_haar", 0.90, "greater",
     "Haar-field refusal at sigma 0.15 (matched calibration) exceeds 0.90"),
    ("H3", "D/shuffled/acc_ungated", 0.25, "two-sided",
     "label-shuffled recognition equals chance (0.25)"),
    ("H4", "E/s0.15/acc_ungated", 0.40, "less",
     "pure phase wave: recognition accuracy at sigma 0.15 is below 0.40"),
    ("H5", "C/max_overlap/auc_phase_scramble", 0.90, "greater",
     "max-overlap gate AUC against scrambled-phase fields exceeds 0.90"),
    ("H6", "C/diff_auc_max_overlap_minus_wave_scan/time_shift_half_spacing",
     0.0, "greater",
     "max-overlap gate AUC beats wave_scan on waves between stored phases"),
    ("H7", "C/rule/diff_bal_haar/midpoint_minus_first", 0.0, "two-sided",
     "balanced accuracy vs Haar differs between midpoint and first-best tau"),
    ("H8", "D/refuse_global_phase_rotation", 0.01, "less",
     "a globally phase-rotated stored wave is accepted (>0.99): known blind "
     "spot"),
    ("H9", "D/refuse_time_shift_half_spacing", 0.50, "less",
     "a wave between stored phases is refused less than half the time"),
]

PROPORTION_LAST = ("acc_ungated", "acc_gated", "accept_in")


def trials_for(key):
    """Trials per replicate behind a proportion key, or None."""
    if not key.split("/")[0] in ("A", "D", "E", "F"):
        return None
    last = key.rsplit("/", 1)[1]
    if last in PROPORTION_LAST:
        return N_EVAL_IN
    if last.startswith("refuse_"):
        return N_EVAL_OOD
    return None


def _summ(args):
    key, vals, resamples = args
    m, lo, hi = bootstrap_ci(vals, rng_for("boot", key), resamples)
    row = {"mean": round(m, 6), "lo": round(lo, 6), "hi": round(hi, 6)}
    t = trials_for(key)
    if t is not None and 0.0 <= m <= 1.0:
        n_total = t * len(vals)
        k = int(round(m * n_total))
        wlo, whi = wilson_interval(k, n_total)
        row["wilson_lo"] = round(wlo, 6)
        row["wilson_hi"] = round(whi, 6)
        row["trials"] = n_total
    return key, row


def _test(args):
    hid, key, null, alt, vals, resamples = args
    p = bootstrap_p(vals, null, rng_for("boot", "test", hid), resamples, alt)
    return hid, p


def run(set_name, jobs, ci_resamples, test_resamples):
    seeds = SEED_SETS[set_name]
    ctx = multiprocessing.get_context("fork") if jobs > 1 else None
    if jobs > 1:
        with ctx.Pool(jobs) as pool:
            reps = pool.map(replicate, seeds, chunksize=1)
    else:
        reps = [replicate(s) for s in seeds]
    keys = sorted(reps[0])
    assert all(sorted(r) == keys for r in reps), "replicates disagree on keys"
    series = {k: [r[k] for r in reps] for k in keys}
    work = [(k, series[k], ci_resamples) for k in keys]
    if jobs > 1:
        with ctx.Pool(jobs) as pool:
            rows = dict(pool.map(_summ, work, chunksize=8))
    else:
        rows = dict(map(_summ, work))
    tests = [(hid, key, null, alt, series[key], test_resamples)
             for hid, key, null, alt, _ in HYPOTHESES]
    if jobs > 1:
        with ctx.Pool(min(jobs, len(tests))) as pool:
            pvals = dict(pool.map(_test, tests))
    else:
        pvals = dict(map(_test, tests))
    adj = holm([pvals[h[0]] for h in HYPOTHESES])
    hyps = []
    for (hid, key, null, alt, text), a in zip(HYPOTHESES, adj):
        hyps.append({
            "id": hid, "key": key, "null": null, "alternative": alt,
            "statement": text, "mean": rows[key]["mean"],
            "lo": rows[key]["lo"], "hi": rows[key]["hi"],
            "p": round(pvals[hid], 6), "p_holm": round(a, 6),
            "supported": a < 0.05,
        })
    return {
        "meta": {
            "set": set_name, "seeds": [seeds[0], seeds[-1]],
            "replicates": len(seeds), "version": __version__,
            "ci_resamples": ci_resamples, "test_resamples": test_resamples,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "protocol": "docs/PROTOCOL.md",
            "synthetic": True,
        },
        "hypotheses": hyps,
        "rows": {k: rows[k] for k in keys},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", choices=sorted(SEED_SETS), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args(argv)
    smoke = args.set == "smoke"
    result = run(args.set, 1 if smoke else args.jobs,
                 200 if smoke else 5000, 500 if smoke else 10000)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"wrote {args.out}: {len(result['rows'])} rows, "
          f"{result['meta']['replicates']} replicates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
