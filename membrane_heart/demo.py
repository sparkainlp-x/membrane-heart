"""Demo for membrane-heart v0.1.0. Run: python demo.py

Builds a 64-neuron heart (seed 42), stores 4 beat phases in the
membrane, calibrates the refusal gate, then reports: geometry,
calibration, clean/noisy recognition, and coherence of a perfect
wave vs a scrambled one.
"""

import random

from .core import MembraneHeart, noisy, rand_field


def main():
    heart = MembraneHeart(n=64, seed=42)
    geo = heart.geometry
    print(f"membrane-heart v0.1.0 — {len(geo.neurons)} neurons, "
          f"{len(geo.edges)} edges, pacemaker {geo.pacemaker_id}")
    print(f"delays: first 0.00, median "
          f"{sorted(geo.delays)[32]:.2f}, last {max(geo.delays):.2f}")

    rng = random.Random(11)
    in_probes = [noisy(heart.field((k % 4) * 10.0), 0.15, rng)
                 for k in range(100)]
    ood_probes = [rand_field(64, rng) for _ in range(100)]
    tau, j = heart.calibrate(in_probes, ood_probes)
    print(f"gate calibrated: tau = {tau:.3f}, Youden J = {j:.3f} (frozen)")

    rng2 = random.Random(99)
    ok = sum(
        1 for k in range(40)
        if heart.decide(noisy(heart.field((k % 4) * 10.0), 0.15,
                              rng2))[1] == heart.PHASE_NAMES[k % 4])
    print(f"fresh noisy recognition (sigma=0.15): {ok}/40")
    rej = sum(
        1 for k in range(50)
        if heart.decide(heart.scrambled_field(1000 + k))[0] == "reject")
    print(f"fresh scrambled fields refused: {rej}/50")
    print(f"coherence: perfect wave "
          f"{heart.coherence(heart.field(5.0), 5.0):.3f}, "
          f"scrambled {heart.coherence(heart.scrambled_field(123), 5.0):.3f}")


if __name__ == "__main__":
    main()
