import contextlib
import io
import json
import os
import subprocess
import sys
import unittest

import membrane_heart
from membrane_heart.demo import format_demo, main, run_demo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestDemo(unittest.TestCase):
    def test_supplied_readme_numbers_reproduce_with_legacy_generator(self):
        r = run_demo(42, legacy_scrambled=True)
        self.assertEqual((r["neurons"], r["edges"], r["pacemaker"]),
                         (64, 156, 0))
        self.assertEqual(f"{r['delay_median']:.2f}", "17.52")
        self.assertEqual(f"{r['delay_last']:.2f}", "31.90")
        self.assertEqual(f"{r['tau']:.3f}", "0.351")
        self.assertEqual(f"{r['youden_j']:.3f}", "1.000")
        self.assertEqual(r["recognised"], 39)
        self.assertEqual(r["refused"], 50)
        self.assertEqual(f"{r['coherence_wave']:.3f}", "1.000")
        self.assertEqual(f"{r['coherence_scrambled']:.3f}", "0.146")

    def test_fixed_generator_changes_only_the_scrambled_coherence(self):
        r = run_demo(42)
        self.assertEqual(r["recognised"], 39)
        self.assertEqual(r["refused"], 50)
        self.assertEqual(f"{r['coherence_scrambled']:.3f}", "0.078")

    def test_ungated_recognition_is_40_of_40_at_seed_42(self):
        self.assertEqual(run_demo(42)["recognised_ungated"], 40)

    def test_run_demo_is_deterministic(self):
        self.assertEqual(run_demo(42), run_demo(42))
        self.assertEqual(format_demo(run_demo(5)), format_demo(run_demo(5)))

    def test_format_mentions_synthetic_and_not_medical(self):
        text = format_demo(run_demo(42))
        self.assertIn("SYNTHETIC", text)
        self.assertIn("Not a medical model", text)


class TestCli(unittest.TestCase):
    def run_main(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_main_text(self):
        code, out = self.run_main([])
        self.assertEqual(code, 0)
        self.assertIn("gate calibrated", out)

    def test_main_json(self):
        code, out = self.run_main(["--json"])
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(data["seed"], 42)

    def test_main_version(self):
        code, out = self.run_main(["--version"])
        self.assertEqual(out.strip(), membrane_heart.__version__)

    def test_module_entry_point_subprocess(self):
        proc = subprocess.run(
            [sys.executable, "-m", "membrane_heart", "--seed", "7"],
            cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("fresh scrambled fields refused", proc.stdout)

    def test_demo_py_shim_subprocess(self):
        proc = subprocess.run([sys.executable, "demo.py", "--version"],
                              cwd=ROOT, capture_output=True, text=True,
                              timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), membrane_heart.__version__)

    def test_bad_flag_exits_nonzero(self):
        proc = subprocess.run([sys.executable, "-m", "membrane_heart",
                               "--nope"], cwd=ROOT, capture_output=True,
                              text=True, timeout=60)
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
