"""Small, dependency-free statistics helpers (SYNTHETIC-study use only).

Everything here is deterministic given an explicit ``random.Random``.
"""

import hashlib
import math
import random

Z95 = 1.959963984540054  # two-sided 95 % normal quantile


def derive_seed(role, *parts):
    """Deterministic 64-bit seed from a role label and parts.

    Different roles ("cal", "eval", "boot", ...) give unrelated
    streams for the same replicate seed, so calibration and
    evaluation probes can never share a random stream.
    """
    text = "|".join([str(role)] + [repr(p) for p in parts])
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def rng_for(role, *parts):
    return random.Random(derive_seed(role, *parts))


def mean(values):
    values = list(values)
    if not values:
        raise ValueError("mean of empty sequence")
    return math.fsum(values) / len(values)


def stdev(values):
    """Sample standard deviation (n - 1); 0.0 for fewer than 2 values."""
    values = list(values)
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(math.fsum((v - m) ** 2 for v in values)
                     / (len(values) - 1))


def wilson_interval(k, n, z=Z95):
    """Wilson score interval for a binomial proportion k/n."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= k <= n:
        raise ValueError("need 0 <= k <= n")
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def bootstrap_means(values, rng, resamples=5000):
    """Bootstrap distribution of the mean (sorted list)."""
    values = list(values)
    n = len(values)
    if n == 0:
        raise ValueError("bootstrap of empty sequence")
    out = []
    for _ in range(resamples):
        out.append(math.fsum(rng.choices(values, k=n)) / n)
    out.sort()
    return out


def percentile(sorted_values, q):
    """Linear-interpolated percentile, q in [0, 1]."""
    if not sorted_values:
        raise ValueError("percentile of empty sequence")
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must be in [0, 1]")
    pos = q * (len(sorted_values) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def bootstrap_ci(values, rng, resamples=5000, alpha=0.05):
    """(mean, lo, hi): percentile bootstrap CI of the mean."""
    dist = bootstrap_means(values, rng, resamples)
    return (mean(values), percentile(dist, alpha / 2),
            percentile(dist, 1 - alpha / 2))


def bootstrap_p(values, null, rng, resamples=5000, alternative="greater"):
    """Bootstrap p-value for H0: mean == null.

    The replicate values are shifted to have mean ``null`` (so the
    resampling distribution is generated under H0), and the observed
    mean is compared with it. ``alternative`` is "greater", "less" or
    "two-sided". The +1 correction keeps p strictly positive.
    """
    values = list(values)
    obs = mean(values)
    shifted = [v - obs + null for v in values]
    dist = bootstrap_means(shifted, rng, resamples)
    if alternative == "greater":
        ge = sum(1 for d in dist if d >= obs)
        return (ge + 1) / (resamples + 1)
    if alternative == "less":
        le = sum(1 for d in dist if d <= obs)
        return (le + 1) / (resamples + 1)
    if alternative == "two-sided":
        ge = sum(1 for d in dist if d - null >= abs(obs - null))
        le = sum(1 for d in dist if d - null <= -abs(obs - null))
        return min(1.0, (ge + le + 1) / (resamples + 1))
    raise ValueError("alternative must be greater, less or two-sided")


def holm(pvalues):
    """Holm-Bonferroni adjusted p-values, in the input order."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = min(1.0, (m - rank) * pvalues[idx])
        running = max(running, val)
        adjusted[idx] = running
    return adjusted


def roc_auc(positive, negative):
    """P(score_pos > score_neg) + 0.5 P(tie): Mann-Whitney AUC.

    ``positive`` should score HIGHER than ``negative`` for a good
    detector of the positive class.
    """
    pos = list(positive)
    neg = list(negative)
    if not pos or not neg:
        raise ValueError("both classes need at least one score")
    tagged = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    # average ranks with ties
    ranks_pos = 0.0
    i = 0
    n = len(tagged)
    while i < n:
        j = i
        while j + 1 < n and tagged[j + 1][0] == tagged[i][0]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        ranks_pos += avg_rank * sum(1 for t in tagged[i:j + 1] if t[1] == 1)
        i = j + 1
    u = ranks_pos - len(pos) * (len(pos) + 1) / 2.0
    return u / (len(pos) * len(neg))
