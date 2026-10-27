import math
import random
import unittest

from membrane_heart import stats


class TestStats(unittest.TestCase):
    def test_wilson_known_values(self):
        lo, hi = stats.wilson_interval(8, 10)
        self.assertAlmostEqual(lo, 0.4902, places=3)
        self.assertAlmostEqual(hi, 0.9433, places=3)

    def test_wilson_zero_and_all(self):
        lo, hi = stats.wilson_interval(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.2775, places=3)
        lo, hi = stats.wilson_interval(10, 10)
        self.assertAlmostEqual(lo, 0.7225, places=3)
        self.assertAlmostEqual(hi, 1.0, places=12)

    def test_wilson_bad_input(self):
        with self.assertRaises(ValueError):
            stats.wilson_interval(1, 0)
        with self.assertRaises(ValueError):
            stats.wilson_interval(11, 10)
        with self.assertRaises(ValueError):
            stats.wilson_interval(-1, 10)

    def test_holm_known_values(self):
        adj = stats.holm([0.03, 0.04, 0.01, 0.005])
        self.assertEqual([round(a, 6) for a in adj],
                         [0.06, 0.06, 0.03, 0.02])

    def test_holm_caps_at_one_and_keeps_order(self):
        adj = stats.holm([0.5, 0.9])
        self.assertEqual(adj, [1.0, 1.0])
        self.assertEqual(stats.holm([]), [])

    def test_holm_never_below_raw(self):
        rng = random.Random(1)
        ps = [rng.random() for _ in range(12)]
        for p, a in zip(ps, stats.holm(ps)):
            self.assertGreaterEqual(a, p)

    def test_auc_known_value(self):
        self.assertAlmostEqual(stats.roc_auc([1, 2, 3], [0, 2]), 0.75)

    def test_auc_extremes_and_ties(self):
        self.assertEqual(stats.roc_auc([2, 3], [0, 1]), 1.0)
        self.assertEqual(stats.roc_auc([0, 1], [2, 3]), 0.0)
        self.assertEqual(stats.roc_auc([1, 1], [1, 1]), 0.5)

    def test_auc_matches_brute_force(self):
        rng = random.Random(5)
        pos = [rng.randint(0, 5) for _ in range(30)]
        neg = [rng.randint(0, 5) for _ in range(25)]
        brute = sum((p > q) + 0.5 * (p == q)
                    for p in pos for q in neg) / (30 * 25)
        self.assertAlmostEqual(stats.roc_auc(pos, neg), brute)

    def test_auc_empty_raises(self):
        with self.assertRaises(ValueError):
            stats.roc_auc([], [1])

    def test_mean_stdev(self):
        self.assertEqual(stats.mean([1, 2, 3]), 2.0)
        self.assertAlmostEqual(stats.stdev([2, 4, 4, 4, 5, 5, 7, 9]),
                               2.138089935, places=6)
        self.assertEqual(stats.stdev([5]), 0.0)
        with self.assertRaises(ValueError):
            stats.mean([])

    def test_percentile(self):
        self.assertEqual(stats.percentile([1, 2, 3, 4], 0.0), 1)
        self.assertEqual(stats.percentile([1, 2, 3, 4], 1.0), 4)
        self.assertAlmostEqual(stats.percentile([1, 2, 3, 4], 0.5), 2.5)

    def test_bootstrap_ci_constant_data(self):
        m, lo, hi = stats.bootstrap_ci([0.5] * 20, random.Random(0), 200)
        self.assertEqual((m, lo, hi), (0.5, 0.5, 0.5))

    def test_bootstrap_ci_brackets_mean_and_is_deterministic(self):
        vals = [random.Random(i).random() for i in range(60)]
        a = stats.bootstrap_ci(vals, random.Random(9), 500)
        b = stats.bootstrap_ci(vals, random.Random(9), 500)
        self.assertEqual(a, b)
        self.assertLessEqual(a[1], a[0])
        self.assertGreaterEqual(a[2], a[0])

    def test_bootstrap_p_directions(self):
        vals = [0.9 + 0.01 * ((i % 5) - 2) for i in range(50)]
        p_hi = stats.bootstrap_p(vals, 0.5, random.Random(1), 500, "greater")
        p_lo = stats.bootstrap_p(vals, 0.5, random.Random(1), 500, "less")
        p_two = stats.bootstrap_p(vals, 0.5, random.Random(1), 500,
                                  "two-sided")
        self.assertLess(p_hi, 0.01)
        self.assertGreater(p_lo, 0.9)
        self.assertLess(p_two, 0.01)
        with self.assertRaises(ValueError):
            stats.bootstrap_p(vals, 0.5, random.Random(1), 10, "bad")

    def test_derive_seed_roles_differ_and_are_stable(self):
        self.assertEqual(stats.derive_seed("cal", 1), stats.derive_seed("cal", 1))
        self.assertNotEqual(stats.derive_seed("cal", 1),
                            stats.derive_seed("eval", 1))
        self.assertNotEqual(stats.derive_seed("cal", 1),
                            stats.derive_seed("cal", 2))
        # pinned value: protects against accidental scheme changes
        self.assertEqual(stats.derive_seed("cal", 1), 0xA8C4DDB092E5589E)
        self.assertTrue(0 <= stats.derive_seed("x") < 2 ** 64)

    def test_rng_for_reproducible(self):
        a = [stats.rng_for("r", 3).random() for _ in range(2)]
        self.assertEqual(a[0], a[1])
        self.assertTrue(math.isfinite(a[0]))


if __name__ == "__main__":
    unittest.main()
