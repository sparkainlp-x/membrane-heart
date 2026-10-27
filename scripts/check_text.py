#!/usr/bin/env python3
"""Fail if tracked text files break the repository's wording rules.

Checks (stdlib only, no network):
  * overclaiming words and phrases that need a linked source, which
    this repository never has, so they are banned outright;
  * clinical-sounding phrases the toy must never use;
  * emoji and pictographic symbols;
  * README/CI status badges;
  * tracked build or cache files (``__pycache__``, ``*.pyc``).

Usage: python scripts/check_text.py [paths...]
With no paths it checks every file listed by ``git ls-files`` (or, if
git is unavailable, every file under the repository root).
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BANNED = [
    (r"\bproven\b", "overclaim word"),
    (r"\bvalidated\b", "overclaim word"),
    (r"production[- ]ready", "overclaim phrase"),
    (r"quantum advantage", "overclaim phrase"),
    (r"real[- ]world performance", "overclaim phrase"),
    (r"arrhythmia detection", "clinical-sounding phrase"),
    (r"clinical sensitivity", "clinical-sounding phrase"),
    (r"clinical specificity", "clinical-sounding phrase"),
    (r"shields\.io|badge\.svg|badgen\.net", "status badge"),
]
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D"
    "\u2300-\u23FF]")
TEXT_SUFFIXES = (".py", ".md", ".txt", ".cff", ".json", ".yml", ".yaml",
                 ".toml", ".cfg", ".gitignore", "LICENSE")
SKIP_FILES = {os.path.join("scripts", "check_text.py"),
              os.path.join("tests", "test_check_text.py"), "LICENSE"}


def tracked_files():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout
        files = [f for f in out.splitlines() if f]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    found = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for name in names:
            found.append(os.path.relpath(os.path.join(base, name), ROOT))
    return found


def check_file(rel):
    problems = []
    if "__pycache__" in rel.split(os.sep) or rel.endswith(".pyc"):
        problems.append((rel, 0, "tracked cache file"))
        return problems
    if rel in SKIP_FILES or not rel.endswith(TEXT_SUFFIXES):
        return problems
    path = os.path.join(ROOT, rel)
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        problems.append((rel, 0, f"unreadable as UTF-8: {exc}"))
        return problems
    for no, line in enumerate(lines, 1):
        for pattern, why in BANNED:
            if re.search(pattern, line, re.IGNORECASE):
                problems.append((rel, no, f"{why}: /{pattern}/"))
        if EMOJI.search(line):
            problems.append((rel, no, "emoji or pictographic symbol"))
    return problems


def main(argv):
    files = argv[1:] or tracked_files()
    problems = []
    for rel in files:
        problems.extend(check_file(rel))
    for rel, no, why in problems:
        print(f"{rel}:{no}: {why}")
    print(f"checked {len(files)} files, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
