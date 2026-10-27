"""Render docs/RESULTS.md from the committed JSON summaries.

    python -m experiments.render_results            # write docs/RESULTS.md
    python -m experiments.render_results --check    # fail if it differs

Tables are generated; interpretation is hand-written in
docs/interpretation.md and appended unchanged.
"""

import argparse
import json
import os
import sys

from membrane_heart.probes import OOD_KINDS

from .studies import ABLATION_SIGMAS, VARIANTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
SIGMAS_A = ("0.00", "0.05", "0.10", "0.15", "0.20", "0.30", "0.45", "0.60")
GATES = ("max_overlap", "wave_scan", "magnitude_profile")


def load(name):
    path = os.path.join(DOCS, "results", name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def num(x, nd):
    text = f"{x:.{nd}f}"
    return text[1:] if text.startswith("-") and float(text) == 0 else text


def ci(row, nd=3):
    return (f"{num(row['mean'], nd)} [{num(row['lo'], nd)}, "
            f"{num(row['hi'], nd)}]")


def wilson(row, nd=3):
    if "wilson_lo" not in row:
        return "n/a"
    return f"[{row['wilson_lo']:.{nd}f}, {row['wilson_hi']:.{nd}f}]"


def table(header, rows):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def outcome(h):
    if h["id"] == "H3":
        return ("control passes (consistent with chance)" if h["supported"]
                else "control FAILS")
    return "supported" if h["supported"] else "NOT supported"


def classify(mean):
    if mean >= 0.90:
        return "REFUSED"
    if mean < 0.10:
        return "NOT REFUSED"
    return "PARTLY REFUSED"


def render(confirm, dev):
    R = confirm["rows"]
    D = dev["rows"] if dev else {}
    meta = confirm["meta"]
    out = []
    add = out.append
    add("# Results")
    add("")
    add("SYNTHETIC toy; not a medical model, not a medical device, not a "
        "diagnosis. Every number below is a property of a seeded simulation "
        "of random heart-shaped layouts, a synthetic wave, synthetic noise "
        "and synthetic out-of-library fields. Nothing here transfers to real "
        "physiology or real data. Generated from `docs/results/confirm.json` "
        "by `python -m experiments.render_results`; do not edit by hand "
        "(hand-written interpretation is in `docs/interpretation.md`).")
    add("")
    add(f"Protocol: `docs/PROTOCOL.md`, committed before any result "
        f"existed (amendment A1 was committed before the confirmation run). "
        f"Confirmation set: seeds {meta['seeds'][0]} to {meta['seeds'][1]} "
        f"({meta['replicates']} replicates), run once. Development set: "
        + (f"seeds {dev['meta']['seeds'][0]} to {dev['meta']['seeds'][1]}"
           if dev else "not present") +
        ". Intervals are 95 % percentile bootstrap over replicates "
        f"({meta['ci_resamples']} resamples); proportions in brackets "
        "after the text `Wilson` are pooled-trial Wilson intervals and "
        "understate uncertainty. Package version "
        f"{meta['version']}; produced with Python {meta['python']}.")
    add("")
    add("## 1. Pre-registered hypotheses (confirmation seeds)")
    add("")
    rows = []
    devh = {h["id"]: h for h in dev["hypotheses"]} if dev else {}
    for h in confirm["hypotheses"]:
        d = devh.get(h["id"])
        rows.append([
            h["id"], h["statement"],
            f"{h['mean']:.4f} [{h['lo']:.4f}, {h['hi']:.4f}]",
            f"{h['alternative']} vs {h['null']}",
            f"{h['p_holm']:.4f}",
            outcome(h),
            f"{d['mean']:.4f}" if d else "n/a"])
    add(table(["id", "statement", "mean [95% CI]", "test", "Holm p",
               "outcome", "dev mean"], rows))
    add("")
    add("Holm p is adjusted over the nine hypotheses together; H3 is a "
        "null-retention control (amendment A2). A supported hypothesis is a "
        "statement about this simulation only; effect size is in the mean "
        "column and must be read with it (H7 is supported yet tiny; H6 "
        "compares two AUCs that are both far below 0.5).")
    add("")
    add("## 2. Study A: recognition and refusal across noise")
    add("")
    rows = []
    for s in SIGMAS_A:
        p = f"A/s{s}/"
        rows.append([s, ci(R[p + "acc_ungated"]), ci(R[p + "acc_gated"]),
                     ci(R[p + "accept_in"]), ci(R[p + "refuse_haar"]),
                     ci(R[p + "refuse_phase_scramble"]),
                     f"{R[p + 'tau']['mean']:.3f}",
                     f"{R[p + 'j_cal']['mean']:.3f}"])
    add(table(["sigma", "acc ungated", "acc gated", "accept in-library",
               "refuse Haar", "refuse scrambled phase", "tau", "J cal"],
              rows))
    add("")
    add("Chance for four phases is 0.25. The gate is calibrated at the "
        "same sigma as the evaluation (matched). Pooled Wilson interval "
        "for the sigma 0.15 ungated accuracy: "
        f"{wilson(R['A/s0.15/acc_ungated'])}.")
    add("")
    add("## 3. Study B: ablations (paired with the default by seed)")
    add("")
    for sigma in ABLATION_SIGMAS:
        s = f"{sigma:.2f}"
        add(f"### sigma {s}")
        add("")
        rows = []
        for name in VARIANTS:
            p = f"B/s{s}/{name}/"
            diff = (ci(R[p + "diff_acc_ungated"])
                    if p + "diff_acc_ungated" in R else "(default)")
            ph = (R[p + "diff_acc_ungated"].get("p_holm")
                  if p + "diff_acc_ungated" in R else None)
            chance = ""
            if name == "phases_6":
                chance = " (chance 0.167)"
            elif name == "phases_8":
                chance = " (chance 0.125)"
            rows.append([name, ci(R[p + "acc_ungated"]) + chance, diff,
                         "" if ph is None else f"{ph:.4f}",
                         f"{R[p + 'acc_gated']['mean']:.3f}",
                         f"{R[p + 'j_cal']['mean']:.3f}",
                         f"{R[p + 'max_nbr_overlap']['mean']:.3f}"])
        add(table(["variant", "acc ungated", "difference vs default",
                   "Holm p (exploratory)", "acc gated", "J cal",
                   "max neighbour overlap"], rows))
        add("")
    add("`n_32_snr` and `n_128_snr` scale sigma by sqrt(64/n); `n_32` and "
        "`n_128` keep the same absolute sigma. Holm p is exploratory and "
        "adjusted over all ablation differences at both sigmas together.")
    add("")
    add("## 4. Study C: refusal quality and baselines")
    add("")
    add("AUC treats in-library probes (noisy, sigma 0.15) as positive and "
        "out-of-library probes as negative; 0.5 is no separation and values "
        "below 0.5 mean the out-of-library probes score HIGHER than "
        "in-library ones. The trivial `constant` gate has AUC 0.5 and "
        "balanced accuracy 0.5 by construction. Out-of-library probes in "
        "this first table are noise-free.")
    add("")
    for prefix, title in (("C", "noise-free out-of-library probes "
                                "(pre-registered)"),
                          ("Cn", "noise-matched out-of-library probes "
                                 "(sigma 0.15; exploratory, amendment A1)")):
        add(f"### AUC and balanced accuracy, {title}")
        add("")
        rows = []
        for kind in OOD_KINDS:
            rows.append(
                [kind] + [ci(R[f"{prefix}/{g}/auc_{kind}"], 3)
                          for g in GATES]
                + [f"{R[f'{prefix}/{g}/bal_{kind}']['mean']:.3f}"
                   for g in GATES])
        add(table(["kind", "AUC max_overlap", "AUC wave_scan",
                   "AUC magnitude_profile", "bal acc max_overlap",
                   "bal acc wave_scan", "bal acc magnitude_profile"], rows))
        add("")
    add("### tau rules, held-out balanced accuracy (sigma 0.15)")
    add("")
    rows = []
    for strat in ("midpoint", "first", "midpoint_all", "median"):
        p = f"C/rule/{strat}/"
        rows.append([strat, f"{R[p + 'tau']['mean']:.3f}",
                     ci(R[p + "accept_in"]), ci(R[p + "bal_haar"], 4),
                     ci(R[p + "bal_phase_scramble"], 4)])
    add(table(["rule", "mean tau", "accept in-library", "bal acc vs Haar",
               "bal acc vs scrambled phase"], rows))
    add("")
    add("Paired differences (midpoint minus other), balanced accuracy vs "
        "Haar: " + "; ".join(
            f"{s}: {ci(R[f'C/rule/diff_bal_haar/midpoint_minus_{s}'], 4)}"
            for s in ("first", "midpoint_all", "median")) + ".")
    add("")
    add("## 5. Study D: negative controls and out-of-library kinds")
    add("")
    add(f"Label-shuffled recognition (chance "
        f"{R['D/shuffled/chance']['mean']:.2f}): "
        f"{ci(R['D/shuffled/acc_ungated'], 4)}. In-library acceptance of "
        f"the frozen gate: {ci(R['D/accept_in'])}.")
    add("")
    add("Classification rule (pre-registered): REFUSED at mean refusal "
        "0.90 or more, NOT REFUSED below 0.10, otherwise PARTLY REFUSED.")
    add("")
    rows = []
    for kind in OOD_KINDS:
        a, b = R[f"D/refuse_{kind}"], R[f"D/noisy/refuse_{kind}"]
        rows.append([kind, ci(a), classify(a["mean"]),
                     f"{R[f'D/max_overlap_{kind}']['mean']:.3f}",
                     ci(b), classify(b["mean"]),
                     f"{R[f'D/noisy/max_overlap_{kind}']['mean']:.3f}"])
    add(table(["kind", "refusal (noise-free)", "class", "mean max overlap",
               "refusal (noise-matched)", "class", "mean max overlap"], rows))
    add("")
    add(f"Mean max overlap of in-library probes: "
        f"{R['D/max_overlap_in']['mean']:.3f}.")
    add("")
    add("## 6. Study E: null, a pure phase wave stored (envelope off)")
    add("")
    rows = []
    for s in ("0.00", "0.05", "0.15"):
        p = f"E/s{s}/"
        rows.append([s, ci(R[p + "acc_ungated"]), ci(R[p + "acc_gated"]),
                     ci(R[p + "frac_index0"]), ci(R[p + "refuse_haar"]),
                     f"{R[p + 'j_cal']['mean']:.3f}",
                     f"{R[p + 'max_nbr_overlap']['mean']:.3f}"])
    add(table(["sigma", "acc ungated", "acc gated",
               "fraction assigned to phase 0", "refuse Haar", "J cal",
               "max neighbour overlap"], rows))
    add("")
    add("The four stored snapshots differ only by a global phase, so every "
        "stored pattern gives the same |overlap| up to floating-point "
        "rounding. Which phase wins is then decided by rounding and by the "
        "tie rule (lowest index), and this column can differ across "
        "platforms; it does not mean the memory recognises anything. The "
        "gate still works as an accept/refuse test of wave-likeness.")
    add("")
    add("## 7. Study F: robustness map of the frozen gate")
    add("")
    add("Rows: calibration sigma (tau is frozen there). Columns: "
        "in-library acceptance at the evaluation sigma.")
    add("")
    rows = []
    for sc in ("0.05", "0.15", "0.30"):
        p = f"F/c{sc}/"
        rows.append([sc, f"{R[p + 'tau']['mean']:.3f}",
                     f"{R[p + 'j_cal']['mean']:.3f}",
                     f"{R[p + 'refuse_haar']['mean']:.3f}"]
                    + [f"{R[p + 'e' + se + '/accept_in']['mean']:.3f}"
                       for se in ("0.00", "0.05", "0.15", "0.30", "0.45",
                                  "0.60")])
    add(table(["calibrated at", "tau", "J cal", "refuse Haar", "accept @0.00",
               "@0.05", "@0.15", "@0.30", "@0.45", "@0.60"], rows))
    add("")
    add("Tau by matched calibration sigma (study A): "
        + ", ".join(f"{s}: {R[f'A/s{s}/tau']['mean']:.3f}"
                    for s in SIGMAS_A) + ".")
    add("")
    add("## 8. Study G: does the phase structure matter?")
    add("")
    rows = []
    for s in SIGMAS_A:
        p = f"G/s{s}/"
        rows.append([s, ci(R[p + "acc_complex"]),
                     ci(R[p + "acc_magnitude_only"]),
                     ci(R[p + "diff_complex_minus_magnitude_only"])])
    add(table(["sigma", "complex projection", "magnitude-only classifier",
               "difference"], rows))
    add("")
    frag = os.path.join(DOCS, "interpretation.md")
    if os.path.exists(frag):
        with open(frag, encoding="utf-8") as fh:
            add(fh.read().rstrip())
        add("")
    return "\n".join(out)


README_BEGIN = "<!-- results:begin -->"
README_END = "<!-- results:end -->"


def readme_block(confirm):
    """Headline table for the README, generated from the JSON."""
    R = confirm["rows"]
    rows = [
        ("Recognition accuracy, sigma 0.15", "A/s0.15/acc_ungated"),
        ("Recognition accuracy, sigma 0.30", "A/s0.30/acc_ungated"),
        ("Recognition accuracy, sigma 0.60 (chance 0.25)",
         "A/s0.60/acc_ungated"),
        ("Haar-random fields refused, sigma 0.15", "A/s0.15/refuse_haar"),
        ("Scrambled-phase fields refused, sigma 0.15",
         "A/s0.15/refuse_phase_scramble"),
        ("Label-shuffled recognition (chance 0.25)", "D/shuffled/acc_ungated"),
        ("Pure phase wave stored, recognition (null; chance 0.25)",
         "E/s0.15/acc_ungated"),
        ("Time-shifted wave between stored phases refused (noise-free)",
         "D/refuse_time_shift_half_spacing"),
        ("Half-masked wave refused (noise-free)",
         "D/refuse_partial_random_half"),
        ("Globally phase-rotated stored wave refused (blind spot)",
         "D/refuse_global_phase_rotation"),
        ("Time-shifted wave refused, noise matched to in-library",
         "D/noisy/refuse_time_shift_half_spacing"),
    ]
    lines = [README_BEGIN,
             f"Confirmation seeds {confirm['meta']['seeds'][0]} to "
             f"{confirm['meta']['seeds'][1]} "
             f"({confirm['meta']['replicates']} random layouts), 95 % "
             "bootstrap intervals over layouts, all SYNTHETIC. Full tables, "
             "ablations, baselines and limits: `docs/RESULTS.md`.",
             ""]
    lines.append(table(["Quantity", "Mean [95% interval]"],
                       [[name, ci(R[key])] for name, key in rows]))
    lines.append("")
    lines.append("All nine pre-registered hypotheses were met on the "
                 "confirmation seeds (`docs/RESULTS.md`, section 1). The "
                 "gate separates random-like fields from stored waves and "
                 "does not reliably refuse deformed stored waves; this is a "
                 "finding about the toy, not about any heart.")
    lines.append(README_END)
    return "\n".join(lines)


def apply_readme(readme_text, confirm):
    a = readme_text.index(README_BEGIN)
    b = readme_text.index(README_END) + len(README_END)
    return readme_text[:a] + readme_block(confirm) + readme_text[b:]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    confirm = load("confirm.json")
    if confirm is None:
        print("docs/results/confirm.json not found", file=sys.stderr)
        return 2
    text = render(confirm, load("dev.json"))
    target = os.path.join(DOCS, "RESULTS.md")
    readme = os.path.join(ROOT, "README.md")
    with open(readme, encoding="utf-8") as fh:
        readme_now = fh.read()
    readme_new = apply_readme(readme_now, confirm)
    if args.check:
        with open(target, encoding="utf-8") as fh:
            current = fh.read()
        if current != text or readme_now != readme_new:
            print("docs/RESULTS.md or the README results block is out of "
                  "date; run python -m experiments.render_results",
                  file=sys.stderr)
            return 1
        print("docs/RESULTS.md and README results match the committed "
              "results")
        return 0
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(readme, "w", encoding="utf-8") as fh:
        fh.write(readme_new)
    print(f"wrote {target} and the README results block")
    return 0


if __name__ == "__main__":
    sys.exit(main())
