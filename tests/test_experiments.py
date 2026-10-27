import unittest

from experiments import run_all
from experiments.common import (N_CAL_IN, N_EVAL_IN, SEED_SETS, cal_probes,
                                calibrated_heart, eval_in, eval_ood,
                                build_heart, recognition)
from experiments.studies import VARIANTS, replicate
from membrane_heart.probes import OOD_KINDS
from membrane_heart.stats import rng_for


class TestSeedDiscipline(unittest.TestCase):
    def test_seed_sets_are_disjoint_and_exclude_demo_seed(self):
        sets = {k: set(v) for k, v in SEED_SETS.items()}
        names = sorted(sets)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                self.assertFalse(sets[a] & sets[b], (a, b))
        for s in sets.values():
            self.assertNotIn(42, s)
        self.assertEqual(len(SEED_SETS["dev"]), 200)
        self.assertEqual(len(SEED_SETS["confirm"]), 200)

    def test_calibration_and_evaluation_streams_never_collide(self):
        seen = {}
        for seed in SEED_SETS["dev"] + SEED_SETS["confirm"]:
            for role in ("cal", "eval", "shuffle", "boot"):
                first = rng_for(role, seed, "0.15").getrandbits(64)
                self.assertNotIn(first, seen)
                seen[first] = (role, seed)

    def test_calibration_probes_differ_from_evaluation_probes(self):
        heart = build_heart(5000)
        cal_in, cal_ood = cal_probes(heart, 5000, 0.15)
        ev_in, _ = eval_in(heart, 5000, 0.15)
        cal_set = {tuple(f) for f in cal_in + cal_ood}
        self.assertFalse(any(tuple(f) in cal_set for f in ev_in))
        for kind in OOD_KINDS:
            if kind in ("global_phase_rotation",):
                continue
            ood = eval_ood(heart, 5000, kind)
            self.assertFalse(any(tuple(f) in cal_set for f in ood), kind)

    def test_eval_sets_are_reproducible(self):
        heart = build_heart(1000)
        a, la = eval_in(heart, 1000, 0.3)
        b, lb = eval_in(heart, 1000, 0.3)
        self.assertEqual((a, la), (b, lb))
        self.assertEqual(la[:5], [0, 1, 2, 3, 0])
        self.assertEqual(len(a), N_EVAL_IN)
        self.assertEqual(len(cal_probes(heart, 1000, 0.3)[0]), N_CAL_IN)

    def test_recognition_counts_ties_to_index_zero(self):
        h = build_heart(9001, envelope=False)
        probes = [h.patterns[i] for i in range(4)]
        ung, gat, idx0 = recognition(h, probes, [0, 1, 2, 3])
        self.assertEqual(idx0, 1.0)
        self.assertEqual(ung, 0.25)


class TestStudies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = replicate(9001)

    def test_replicate_is_deterministic(self):
        self.assertEqual(self.a, replicate(9001))

    def test_replicate_values_are_finite_floats(self):
        import math
        for k, v in self.a.items():
            self.assertTrue(isinstance(v, float) and math.isfinite(v), k)

    def test_proportions_in_unit_interval(self):
        for k, v in self.a.items():
            last = k.rsplit("/", 1)[1]
            if last.startswith(("acc_", "accept_", "refuse_", "auc_", "bal_")):
                self.assertTrue(0.0 <= v <= 1.0, (k, v))

    def test_hypothesis_keys_exist(self):
        for hid, key, *_ in run_all.HYPOTHESES:
            self.assertIn(key, self.a, hid)

    def test_all_variants_and_kinds_present(self):
        for name in VARIANTS:
            self.assertIn(f"B/s0.15/{name}/acc_ungated", self.a)
        for kind in OOD_KINDS:
            self.assertIn(f"D/refuse_{kind}", self.a)
            self.assertIn(f"C/max_overlap/auc_{kind}", self.a)

    def test_noise_matched_and_magnitude_only_keys_present(self):
        for kind in OOD_KINDS:
            self.assertIn(f"D/noisy/refuse_{kind}", self.a)
            self.assertIn(f"Cn/max_overlap/auc_{kind}", self.a)
        self.assertIn("G/s0.15/acc_magnitude_only", self.a)
        self.assertAlmostEqual(
            self.a["G/s0.15/diff_complex_minus_magnitude_only"],
            self.a["G/s0.15/acc_complex"]
            - self.a["G/s0.15/acc_magnitude_only"], places=12)

    def test_noise_matched_rotation_is_like_in_library(self):
        # a globally rotated stored wave plus the same noise is a
        # statistically ordinary in-library probe: refusal ~ 1 - accept
        self.assertLess(abs(self.a["D/noisy/refuse_global_phase_rotation"]
                            - (1 - self.a["D/accept_in"])), 0.15)

    def test_default_ablation_equals_study_a(self):
        self.assertEqual(self.a["B/s0.15/default/acc_ungated"],
                         self.a["A/s0.15/acc_ungated"])
        self.assertEqual(self.a["F/c0.15/tau"], self.a["A/s0.15/tau"])

    def test_global_phase_rotation_is_never_refused(self):
        self.assertEqual(self.a["D/refuse_global_phase_rotation"], 0.0)

    def test_pure_phase_null_is_chance_like(self):
        self.assertLess(self.a["E/s0.15/acc_ungated"], 0.45)
        self.assertEqual(self.a["E/s0.15/max_nbr_overlap"], 1.0)

    def test_pinned_values_are_identical_on_every_python_version(self):
        # Guards cross-version drift (exactly rounded sums are used so
        # that Python 3.10 to 3.13 agree, including tie-dependent keys).
        pinned = {
            "A/s0.15/tau": 0.326733,
            "A/s0.15/acc_ungated": 0.99,
            "A/s0.30/acc_gated": 0.78,
            "E/s0.15/frac_index0": 0.71,
            "A/s0.00/tau": 0.638614,
            "G/s0.30/acc_magnitude_only": 0.49,
            "D/refuse_conjugate_wave": 0.0,
        }
        for key, value in pinned.items():
            self.assertAlmostEqual(self.a[key], value, places=6, msg=key)

    def test_trials_for(self):
        self.assertEqual(run_all.trials_for("A/s0.15/acc_ungated"), 100)
        self.assertEqual(run_all.trials_for("D/refuse_haar"), 50)
        self.assertIsNone(run_all.trials_for("B/s0.15/default/acc_ungated"))
        self.assertIsNone(run_all.trials_for("A/s0.15/tau"))


class TestEvalOod(unittest.TestCase):
    def test_noise_free_stream_unchanged_and_noisy_differs(self):
        heart = build_heart(9001)
        a = eval_ood(heart, 9001, "haar")
        b = eval_ood(heart, 9001, "haar", 0.0)
        c = eval_ood(heart, 9001, "haar", 0.15)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(len(c), 50)

    def test_noisy_fields_are_unit_norm(self):
        heart = build_heart(9001)
        for f in eval_ood(heart, 9001, "conjugate_wave", 0.15):
            self.assertAlmostEqual(sum(abs(x) ** 2 for x in f), 1.0, places=9)


class TestMagnitudeOnly(unittest.TestCase):
    def test_classifies_clean_patterns_and_zero_field(self):
        from membrane_heart.probes import GateScores
        heart = build_heart(9001)
        gs = GateScores(heart, scan_points=4)
        for i, p in enumerate(heart.patterns):
            self.assertEqual(gs.classify_magnitude_only(p), i)
        self.assertIsNone(gs.classify_magnitude_only([0j] * 64))

    def test_blind_to_global_phase_not_to_the_wave(self):
        from membrane_heart.probes import GateScores
        heart = build_heart(9001, envelope=False)
        gs = GateScores(heart, scan_points=4)
        # pure phase: all magnitudes equal -> ties -> index 0 for all
        self.assertEqual({gs.classify_magnitude_only(p)
                          for p in heart.patterns}, {0})


class TestRunAll(unittest.TestCase):
    def test_hypotheses_ids_unique_and_nine(self):
        ids = [h[0] for h in run_all.HYPOTHESES]
        self.assertEqual(ids, [f"H{i}" for i in range(1, 10)])

    def test_summary_row_has_ci_and_wilson(self):
        key, row = run_all._summ(("A/s0.15/acc_ungated",
                                  [0.9, 1.0, 0.95, 0.97], 100))
        self.assertLessEqual(row["lo"], row["mean"])
        self.assertGreaterEqual(row["hi"], row["mean"])
        self.assertIn("wilson_lo", row)
        self.assertEqual(row["trials"], 400)

    def test_heart_shared_by_calibrated_helper_is_frozen(self):
        heart, tau, j = calibrated_heart(9002, 0.15)
        self.assertEqual(heart.tau, tau)


if __name__ == "__main__":
    unittest.main()


class TestProtocolRules(unittest.TestCase):
    def test_h3_is_null_retention_control(self):
        ok = {"lo": 0.243, "hi": 0.255}
        self.assertTrue(run_all._supported("H3", 0.64, ok))
        self.assertFalse(run_all._supported("H3", 0.01, ok))
        self.assertFalse(run_all._supported("H3", 0.64,
                                            {"lo": 0.20, "hi": 0.255}))
        self.assertFalse(run_all._supported("H3", 0.64,
                                            {"lo": 0.243, "hi": 0.30}))

    def test_other_hypotheses_use_holm_p_below_005(self):
        row = {"lo": 0.0, "hi": 1.0}
        self.assertTrue(run_all._supported("H1", 0.049, row))
        self.assertFalse(run_all._supported("H1", 0.05, row))


class TestRender(unittest.TestCase):
    def test_render_is_deterministic_and_complete(self):
        import json
        import os
        from experiments import render_results as rr
        path = os.path.join(rr.DOCS, "results", "dev.json")
        if not os.path.exists(path):
            self.skipTest("no dev results committed")
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        a, b = rr.render(d, d), rr.render(d, d)
        self.assertEqual(a, b)
        for section in ("## 1.", "## 2.", "## 3.", "## 4.", "## 5.",
                        "## 6.", "## 7.", "## 8."):
            self.assertIn(section, a)
        self.assertIn("SYNTHETIC", a)
        import re
        self.assertIsNone(re.search(r"-0\.0+(?![0-9])", a))

    def test_classify_thresholds(self):
        from experiments.render_results import classify
        self.assertEqual(classify(0.90), "REFUSED")
        self.assertEqual(classify(0.8999), "PARTLY REFUSED")
        self.assertEqual(classify(0.0999), "NOT REFUSED")
        self.assertEqual(classify(0.10), "PARTLY REFUSED")
