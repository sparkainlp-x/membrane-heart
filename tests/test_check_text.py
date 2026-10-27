import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import check_text  # noqa: E402


class TestCheckText(unittest.TestCase):
    def check(self, text, name="note.md"):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            old = check_text.ROOT
            check_text.ROOT = tmp
            try:
                return check_text.check_file(name)
            finally:
                check_text.ROOT = old

    def test_clean_text_passes(self):
        self.assertEqual(self.check("A SYNTHETIC toy. Jean-François.\n"), [])

    def test_banned_words_flagged(self):
        bad = ["This is proven.", "A validated model.", "production-ready",
               "quantum advantage", "real-world performance",
               "arrhythmia detection", "clinical sensitivity"]
        for text in bad:
            self.assertEqual(len(self.check(text)), 1, text)

    def test_word_boundaries_avoid_false_positives(self):
        self.assertEqual(self.check("improvement, unvalidated claims, "
                                    "input validation"), [])

    def test_emoji_and_badges_flagged(self):
        self.assertTrue(self.check("done \U0001F600"))
        self.assertTrue(self.check("check \u2705"))
        self.assertTrue(self.check("![b](https://img.shields.io/x)"))

    def test_em_dash_and_accents_allowed(self):
        self.assertEqual(self.check("a \u2014 b \u00e7 \u2192 c"), [])

    def test_cache_files_flagged(self):
        self.assertTrue(check_text.check_file("pkg/__pycache__/x.pyc"))

    def test_repo_is_clean(self):
        proc = subprocess.run([sys.executable,
                               os.path.join(ROOT, "scripts", "check_text.py")],
                              cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)


if __name__ == "__main__":
    unittest.main()
