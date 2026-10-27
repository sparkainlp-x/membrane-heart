import math
import unittest

from membrane_heart import HeartGeometry, heart_curve_point


class TestGeometry(unittest.TestCase):
    def test_seed42_unchanged_from_supplied_package(self):
        g = HeartGeometry(n=64, seed=42)
        self.assertEqual(len(g.edges), 156)
        self.assertEqual(g.pacemaker_id, 0)
        self.assertEqual(g.bridges, 0)
        self.assertAlmostEqual(sorted(g.delays)[32], 17.52, places=2)
        self.assertAlmostEqual(max(g.delays), 31.90, places=2)

    def test_curve_symmetry(self):
        x1, y1 = heart_curve_point(0.7)
        x2, y2 = heart_curve_point(-0.7)
        self.assertAlmostEqual(x1, -x2)
        self.assertAlmostEqual(y1, y2)

    def test_disconnected_knn_graph_is_bridged_with_finite_delays(self):
        # k=2 leaves many seeds disconnected; the supplied code would
        # produce infinite delays and NaN fields there.
        hit = 0
        for seed in range(40):
            g = HeartGeometry(n=32, seed=seed, k=2)
            self.assertTrue(all(math.isfinite(d) for d in g.delays))
            hit += g.bridges > 0
        self.assertGreater(hit, 0)

    def test_edges_are_sorted_unique_and_symmetric_adjacency(self):
        g = HeartGeometry(n=32, seed=3)
        self.assertEqual(g.edges, sorted(set(g.edges)))
        for a, b in g.edges:
            self.assertIn(b, g.neighbours(a))
            self.assertIn(a, g.neighbours(b))

    def test_neighbours_returns_copy(self):
        g = HeartGeometry(n=16, seed=1)
        nb = g.neighbours(0)
        nb.append(999)
        self.assertNotIn(999, g.neighbours(0))

    def test_pacemaker_position_changes_pacemaker(self):
        a = HeartGeometry(n=64, seed=42)
        b = HeartGeometry(n=64, seed=42, pacemaker_xy=(0.0, -16.0))
        self.assertNotEqual(a.pacemaker_id, b.pacemaker_id)
        self.assertEqual(b.delays[b.pacemaker_id], 0.0)
        self.assertEqual(sum(1 for x in b.neurons if x.kind == "pacemaker"), 1)

    def test_argument_validation(self):
        with self.assertRaises(ValueError):
            HeartGeometry(n=4)
        with self.assertRaises(ValueError):
            HeartGeometry(n=16, k=0)
        with self.assertRaises(ValueError):
            HeartGeometry(n=16, k=16)

    def test_delays_are_shortest_paths(self):
        g = HeartGeometry(n=24, seed=7)
        by_id = {n.id: n for n in g.neurons}
        for a, b in g.edges:
            w = math.hypot(by_id[a].x - by_id[b].x, by_id[a].y - by_id[b].y)
            self.assertLessEqual(abs(g.delays[a] - g.delays[b]), w + 1e-9)

    def test_deterministic_across_builds(self):
        a = HeartGeometry(n=48, seed=5)
        b = HeartGeometry(n=48, seed=5)
        self.assertEqual(a.edges, b.edges)
        self.assertEqual(a.delays, b.delays)


if __name__ == "__main__":
    unittest.main()
