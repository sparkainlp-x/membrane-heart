import os
import re
import unittest

from membrane_heart.demo import format_demo, run_demo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return fh.read()


class TestReadmeClaims(unittest.TestCase):
    def test_demo_block_matches_a_fresh_run(self):
        m = re.search(r"<!-- demo-output:begin -->\n```text\n(.*?)\n```\n"
                      r"<!-- demo-output:end -->", read("README.md"), re.S)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), format_demo(run_demo(42)))

    def test_readme_states_the_required_warnings(self):
        text = read("README.md")
        for needle in ("SYNTHETIC", "Not a medical model",
                       "not a medical device", "not a",
                       "No release, tag or DOI has been issued yet",
                       "AGPL-3.0-only", "Copyright (C) 2026 "
                       "Jean-Fran\u00e7ois Brisson"):
            self.assertIn(needle, text)

    def test_license_is_full_agpl_text(self):
        text = read("LICENSE")
        self.assertIn("GNU AFFERO GENERAL PUBLIC LICENSE", text)
        self.assertIn("Version 3, 19 November 2007", text)
        self.assertIn("END OF TERMS AND CONDITIONS", text)
        self.assertIn("13. Remote Network Interaction", text)
        self.assertGreater(len(text.splitlines()), 600)

    def test_citation_and_zenodo_are_consistent(self):
        cff = read("CITATION.cff")
        zen = read(".zenodo.json")
        py = read("pyproject.toml")
        for text in (cff, zen, py):
            self.assertIn("0.1.0", text)
        self.assertIn("0009-0000-9778-5374", cff)
        self.assertIn("0009-0000-9778-5374", zen)
        self.assertIn("AGPL-3.0-only", cff)
        self.assertIn("AGPL-3.0-only", zen)
        self.assertNotIn("doi:", cff.lower())

    def test_design_keeps_falsified_designs_section(self):
        text = read("DESIGN.md")
        self.assertIn("Falsified", text)
        self.assertIn("Envelope, not pure phase", text)


if __name__ == "__main__":
    unittest.main()


class TestResultsClaims(unittest.TestCase):
    """Numbers quoted in docs/interpretation.md and the README table
    must match docs/results/confirm.json."""

    @classmethod
    def setUpClass(cls):
        import json
        with open(os.path.join(ROOT, "docs", "results", "confirm.json"),
                  encoding="utf-8") as fh:
            cls.conf = json.load(fh)
        cls.rows = cls.conf["rows"]
        cls.text = read("docs/interpretation.md")

    def mean(self, key, nd):
        # signs are carried by words in the text ("loses", "drops")
        return f"{abs(self.rows[key]['mean']):.{nd}f}"

    def test_interpretation_numbers_match_confirm_json(self):
        claims = [
            ("A/s0.30/acc_ungated", 3), ("A/s0.60/acc_ungated", 3),
            ("A/s0.15/acc_gated", 3), ("A/s0.15/refuse_haar", 3),
            ("A/s0.30/refuse_haar", 3), ("A/s0.30/accept_in", 3),
            ("D/shuffled/acc_ungated", 4), ("E/s0.15/acc_ungated", 4),
            ("D/refuse_conjugate_wave", 3),
            ("D/refuse_magnitude_permuted", 3),
            ("D/refuse_phase_scramble_envelope", 3),
            ("D/noisy/refuse_time_shift_half_spacing", 2),
            ("D/noisy/refuse_conjugate_wave", 2),
            ("D/noisy/refuse_magnitude_permuted", 2),
            ("D/noisy/refuse_phase_scramble_envelope", 2),
            ("C/max_overlap/auc_time_shift_half_spacing", 3),
            ("Cn/max_overlap/auc_time_shift_half_spacing", 3),
            ("Cn/wave_scan/auc_time_shift_half_spacing", 3),
            ("C/magnitude_profile/auc_haar", 3),
            ("C/max_overlap/auc_magnitude_permuted", 3),
            ("C/magnitude_profile/auc_magnitude_permuted", 3),
            ("C/rule/diff_bal_haar/midpoint_minus_first", 4),
            ("F/c0.05/e0.15/accept_in", 3), ("F/c0.15/e0.30/accept_in", 3),
            ("B/s0.30/width_64/acc_ungated", 3),
            ("B/s0.30/width_4/diff_acc_ungated", 3),
            ("B/s0.30/phases_8/acc_ungated", 3),
            ("B/s0.15/phases_8/acc_ungated", 3),
            ("B/s0.30/n_128_snr/diff_acc_ungated", 3),
            ("G/s0.30/acc_magnitude_only", 3),
            ("B/s0.30/phases_8/max_nbr_overlap", 2),
            ("B/s0.15/default/max_nbr_overlap", 2),
            ("D/refuse_partial_late_half", 3),
            ("B/s0.30/n_32_snr/diff_acc_ungated", 3),
            ("B/s0.30/width_12/diff_acc_ungated", 3),
            ("G/s0.15/acc_magnitude_only", 3),
            ("C/max_overlap/auc_phase_scramble", 5),
            ("G/s0.30/diff_complex_minus_magnitude_only", 3),
        ]
        for key, nd in claims:
            self.assertTrue(self.mean(key, nd) in self.text,
                            f"{key}: {self.mean(key, nd)} not quoted")

    def test_hypothesis_table_numbers_in_text(self):
        hyps = {h["id"]: h for h in self.conf["hypotheses"]}
        self.assertIn(f"{hyps['H1']['mean']:.4f}", self.text)
        self.assertIn(f"{hyps['H3']['mean']:.4f}", self.text)
        for h in hyps.values():
            self.assertTrue(h["supported"], h["id"])

    def test_results_md_matches_committed_json(self):
        from experiments import render_results as rr
        dev = rr.load("dev.json")
        self.assertEqual(rr.render(self.conf, dev), read("docs/RESULTS.md"))

    def test_readme_results_block_matches_committed_json(self):
        from experiments import render_results as rr
        readme = read("README.md")
        self.assertEqual(rr.apply_readme(readme, self.conf), readme)
        self.assertIn("All nine pre-registered hypotheses were met", readme)

    def test_confirm_set_is_the_preregistered_one(self):
        meta = self.conf["meta"]
        self.assertEqual(meta["seeds"], [5000, 5199])
        self.assertEqual(meta["replicates"], 200)
        self.assertEqual(meta["set"], "confirm")
        self.assertTrue(meta["synthetic"])
