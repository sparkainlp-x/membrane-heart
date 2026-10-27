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
