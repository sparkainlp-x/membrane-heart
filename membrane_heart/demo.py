"""Seeded demo of membrane-heart (SYNTHETIC toy; not a medical model).

Builds a 64-neuron heart-shaped network, stores 4 wave snapshots in
the membrane, calibrates the refusal gate on one random stream and
evaluates on separate streams, then reports geometry, calibration,
noisy recognition, refusal of scrambled fields and coherence.
"""

import json
import random

from .core import (MembraneHeart, __version__, legacy_scrambled_field,
                   noisy, rand_field)

BANNER = ("SYNTHETIC toy. Not a medical model, not a medical device, "
          "not a diagnosis.")


def run_demo(seed=42, legacy_scrambled=False):
    """Return the demo measurements as a dict (deterministic)."""
    heart = MembraneHeart(n=64, seed=seed)
    geo = heart.geometry
    n = heart.n

    def scrambled(s):
        if legacy_scrambled:
            return legacy_scrambled_field(n, s)
        return heart.scrambled_field(s)

    rng = random.Random(11)  # calibration stream
    in_probes = [noisy(heart.patterns[k % 4], 0.15, rng)
                 for k in range(100)]
    ood_probes = [rand_field(n, rng) for _ in range(100)]
    tau, j = heart.calibrate(in_probes, ood_probes)

    rng2 = random.Random(99)  # separate evaluation stream
    probes = [noisy(heart.patterns[k % 4], 0.15, rng2) for k in range(40)]
    # As in v0.1.0: "recognised" = accepted by the gate AND correct.
    ok = sum(1 for k, f in enumerate(probes)
             if heart.decide(f)[1] == heart.phase_names[k % 4])
    ok_ungated = sum(1 for k, f in enumerate(probes)
                     if heart.classify(f) == heart.phase_names[k % 4])
    refused = sum(
        1 for k in range(50)
        if heart.decide(scrambled(1000 + k))[0] == "reject")
    return {
        "version": __version__,
        "seed": seed,
        "legacy_scrambled": legacy_scrambled,
        "neurons": len(geo.neurons),
        "edges": len(geo.edges),
        "pacemaker": geo.pacemaker_id,
        "delay_median": sorted(geo.delays)[n // 2],
        "delay_last": max(geo.delays),
        "tau": tau,
        "youden_j": j,
        "recognised": ok,
        "recognised_ungated": ok_ungated,
        "recognition_trials": 40,
        "refused": refused,
        "refusal_trials": 50,
        "coherence_wave": heart.coherence(heart.field(5.0), 5.0),
        "coherence_scrambled": heart.coherence(scrambled(123), 5.0),
    }


def format_demo(r):
    return "\n".join([
        f"membrane-heart v{r['version']} -- {BANNER}",
        f"{r['neurons']} neurons, {r['edges']} edges, "
        f"pacemaker {r['pacemaker']}",
        f"delays: first 0.00, median {r['delay_median']:.2f}, "
        f"last {r['delay_last']:.2f}",
        f"gate calibrated: tau = {r['tau']:.3f}, "
        f"Youden J = {r['youden_j']:.3f} (frozen)",
        f"fresh noisy recognition (sigma=0.15): "
        f"{r['recognised']}/{r['recognition_trials']} "
        f"(gated; ungated {r['recognised_ungated']}/"
        f"{r['recognition_trials']})",
        f"fresh scrambled fields refused: "
        f"{r['refused']}/{r['refusal_trials']}",
        f"coherence: perfect wave {r['coherence_wave']:.3f}, "
        f"scrambled {r['coherence_scrambled']:.3f}",
    ])


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        prog="python -m membrane_heart",
        description="membrane-heart demo. " + BANNER)
    parser.add_argument("--seed", type=int, default=42,
                        help="geometry seed (default 42)")
    parser.add_argument("--legacy-scrambled", action="store_true",
                        help="use the v0.1.0 scrambled-field generator")
    parser.add_argument("--json", action="store_true",
                        help="print the measurements as JSON")
    parser.add_argument("--version", action="store_true",
                        help="print the version and exit")
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    result = run_demo(args.seed, args.legacy_scrambled)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_demo(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
