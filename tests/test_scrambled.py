import math
import unittest

from membrane_heart import (MembraneHeart, legacy_scrambled_field,
                            phase_scrambled_field)


class TestScrambled(unittest.TestCase):
    def test_phase_scrambled_has_equal_magnitudes(self):
        f = phase_scrambled_field(64, 5)
        mags = [abs(c) for c in f]
        self.assertAlmostEqual(max(mags), min(mags), places=12)
        self.assertAlmostEqual(mags[0], 1 / math.sqrt(64), places=12)

    def test_legacy_scrambled_does_not_have_equal_magnitudes(self):
        # Defect in the supplied v0.1.0 generator: documented, kept.
        f = legacy_scrambled_field(64, 5)
        mags = [abs(c) for c in f]
        self.assertGreater(max(mags) - min(mags), 0.05)

    def test_methods_delegate_and_are_seeded(self):
        h = MembraneHeart(n=32, seed=1)
        self.assertEqual(h.scrambled_field(3), phase_scrambled_field(32, 3))
        self.assertEqual(h.legacy_scrambled_field(3),
                         legacy_scrambled_field(32, 3))
        self.assertNotEqual(h.scrambled_field(3), h.scrambled_field(4))

    def test_scrambled_unit_norm(self):
        f = phase_scrambled_field(40, 9)
        self.assertAlmostEqual(sum(abs(c) ** 2 for c in f), 1.0, places=12)


if __name__ == "__main__":
    unittest.main()
