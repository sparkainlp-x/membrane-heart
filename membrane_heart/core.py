"""membrane-heart v0.1.0 — a sparkainlp-x membrane simulating a heart.

Stdlib-only Python, seeded, reproducible, AGPL-3.0-only.

What is reused, exactly
------------------------
1. Geometry from holo-heart-neurons: the classic parametric heart
   curve, 64 seeded neurons (outline + interior), 4-nearest-neighbour
   edges, a pacemaker, and beat propagation by Dijkstra
   (activation delay = shortest-path distance / velocity).
2. Membrane from membrane-capacity (sparkainlp-x): complex oscillators
   hold a field; patterns are stored as an outer-product holographic
   memory; recognition is one-shot projection — winner = argmax
   |overlap|, probabilities = |m|^2 / sum |m|^2.
3. Gate from refusing-membrane: REJECT iff max |overlap| < tau, with
   tau self-calibrated once (Youden's J) and then frozen. The
   calibration here picks the MIDPOINT of the maximal-J taus, the
   improvement made in membrane-vs-hopfield, not the first best tau
   (which sits on the edge of the separation gap).

What the simulation is
----------------------
A travelling wave, not a heart. The pacemaker fires; the wave reaches
each neuron after its Dijkstra delay. The field at time t is an
enveloped phasor per neuron:

    s_i(t) = (t - delay_i) mod period
    field_i(t) ∝ exp(-s_i(t)^2 / (2 * width^2))
                 * exp(i * 2*pi*(t - delay_i) / period)

with width = 8.0 time units, then normalised to unit length.

Four reference beat phases are stored in the membrane: the fields at
t = 0, period/4, period/2, 3*period/4. A probe field is classified
by projection: which beat phase is this, or — through the gate —
"I don't know" (a scrambled field, whose phases no longer follow the
wave, is refused instead of mislabelled).

A pure phase wave cannot be stored this way — snapshots at different
times differ only by a global phase, and |overlap| is blind to global
phase, so all four snapshots would be indistinguishable (caught by
the first test run: noisy recognition 0.325, not 0.90). The wave
therefore carries an envelope: a neuron is bright just after the
wave passes it and fades behind the wavefront, so each snapshot has
a different amplitude profile and the membrane can tell them apart.

Rhythm coherence measures whether a field still follows the wave:

    coherence(t) = |<field, expected_field(t)>|

Perfect wave: 1.0. Random phases: ~1/sqrt(N) ≈ 0.125 for N=64.

What this is NOT — read before any use
---------------------------------------
Not a human heart. Not cardiac electrophysiology (no ionic currents,
no atria/ventricles, no ECG, no refractory period, no re-entry).
Not a medical device, not a diagnosis, not a measurement of any real
person. The "heart" is a parametric curve; the "beat" is a phase wave;
the "arrhythmia" is a scrambled phase field. Synthetic, toy,
educational — a demonstration that the membrane frame can hold,
recognise, and refuse beat states.
"""

import heapq
import math
import random

__version__ = "0.1.0"

__all__ = [
    "HeartGeometry", "MembraneHeart", "Neuron", "TAU_STRATEGIES",
    "calibrate_tau", "heart_curve_point", "is_finite_field",
    "legacy_scrambled_field", "noisy", "normalize", "overlap",
    "phase_scrambled_field", "rand_field",
]


# ---------------------------------------------------------------- geometry
def heart_curve_point(t):
    """Classic parametric heart curve point at angle t (radians).

    At t=0 this gives (0, 5) — checked by a test.
    """
    return (
        16.0 * math.sin(t) ** 3,
        13.0 * math.cos(t)
        - 5.0 * math.cos(2.0 * t)
        - 2.0 * math.cos(3.0 * t)
        - math.cos(4.0 * t),
    )


def _point_in_polygon(x, y, polygon):
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            x_int = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_int:
                inside = not inside
    return inside


class Neuron:
    def __init__(self, nid, x, y, kind):
        self.id = nid
        self.x = float(x)
        self.y = float(y)
        self.kind = kind

    def __repr__(self):
        return f"Neuron({self.id}, {self.x:.2f}, {self.y:.2f}, {self.kind!r})"


class HeartGeometry:
    """Heart-shaped neuron layout + pacemaker delays (Dijkstra).

    ``pacemaker_xy`` is the point the pacemaker is placed nearest to
    (default (0, 5), as supplied). ``k`` is the number of nearest
    neighbours each neuron links to. If the k-nearest-neighbour graph
    is disconnected (possible for some seeds and small k), the
    closest pair of components is bridged by the shortest edge until
    the graph is connected, so every delay is finite. For connected
    graphs (including seed 42, n=64, k=4) nothing is added.
    """

    def __init__(self, n=64, seed=42, outline_frac=0.6, k=4,
                 pacemaker_xy=(0.0, 5.0)):
        if n < 8:
            raise ValueError("n must be at least 8")
        if not 1 <= k < n:
            raise ValueError("k must satisfy 1 <= k < n")
        self.n = n
        self.seed = seed
        self.k = k
        self.bridges = 0
        rng = random.Random(seed)
        n_outline = max(4, int(round(n * outline_frac)))
        n_inner = n - n_outline
        outline = [
            heart_curve_point(2.0 * math.pi * i / n_outline)
            for i in range(n_outline)
        ]
        neurons = [
            Neuron(i, x, y, "outline") for i, (x, y) in enumerate(outline)
        ]
        inner = []
        attempts = 0
        while len(inner) < n_inner and attempts < 20000:
            attempts += 1
            x = rng.uniform(-17.0, 17.0)
            y = rng.uniform(-17.0, 14.0)
            if _point_in_polygon(x, y, outline):
                inner.append((x, y))
        while len(inner) < n_inner:
            x, y = outline[len(inner) % n_outline]
            inner.append((x * 0.5, y * 0.5))
        for j, (x, y) in enumerate(inner):
            neurons.append(Neuron(n_outline + j, x, y, "inner"))
        px, py = pacemaker_xy
        pacemaker = min(
            neurons,
            key=lambda neu: (neu.x - px) ** 2 + (neu.y - py) ** 2,
        )
        pacemaker.kind = "pacemaker"
        self.pacemaker_id = pacemaker.id
        self.neurons = neurons
        self.edges = self._connect(k)
        self._adj = self._adjacency()
        self.delays = self._delays()

    def _connect(self, k):
        edges = set()
        for a in self.neurons:
            dists = sorted(
                ((a.x - b.x) ** 2 + (a.y - b.y) ** 2, b.id)
                for b in self.neurons
                if b.id != a.id
            )
            for _, bid in dists[:k]:
                edges.add((min(a.id, bid), max(a.id, bid)))
        edges = self._bridge_components(edges)
        return sorted(edges)

    def _components(self, edges):
        parent = list(range(len(self.neurons)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a, b in edges:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
        return [find(i) for i in range(len(self.neurons))]

    def _bridge_components(self, edges):
        while True:
            comp = self._components(edges)
            if len(set(comp)) == 1:
                return edges
            best = None
            for a in self.neurons:
                for b in self.neurons:
                    if a.id < b.id and comp[a.id] != comp[b.id]:
                        d = (a.x - b.x) ** 2 + (a.y - b.y) ** 2
                        if best is None or (d, a.id, b.id) < best:
                            best = (d, a.id, b.id)
            edges.add((best[1], best[2]))
            self.bridges += 1

    def _adjacency(self):
        adj = {neu.id: [] for neu in self.neurons}
        for a, b in self.edges:
            adj[a].append(b)
            adj[b].append(a)
        return {nid: sorted(v) for nid, v in adj.items()}

    def neighbours(self, nid):
        return list(self._adj[nid])

    def _delays(self, velocity=1.0):
        by_id = {neu.id: neu for neu in self.neurons}
        times = {neu.id: math.inf for neu in self.neurons}
        times[self.pacemaker_id] = 0.0
        heap = [(0.0, self.pacemaker_id)]
        while heap:
            t, nid = heapq.heappop(heap)
            if t > times[nid]:
                continue
            a = by_id[nid]
            for mid in self._adj[nid]:
                b = by_id[mid]
                w = math.hypot(a.x - b.x, a.y - b.y) / velocity
                if t + w < times[mid]:
                    times[mid] = t + w
                    heapq.heappush(heap, (times[mid], mid))
        return [times[neu.id] for neu in self.neurons]


# ---------------------------------------------------------------- membrane
def normalize(v):
    # math.fsum (exactly rounded) keeps results identical across Python
    # versions; built-in sum() changed its float summation in 3.12.
    n = math.sqrt(math.fsum(abs(c) ** 2 for c in v))
    if n == 0:
        raise ValueError("cannot normalize a zero vector")
    return [c / n for c in v]


def overlap(field, pattern):
    """<pattern, field> with exactly rounded real and imaginary sums."""
    prods = [p.conjugate() * f for p, f in zip(pattern, field)]
    return complex(math.fsum(c.real for c in prods),
                   math.fsum(c.imag for c in prods))


def is_finite_field(field):
    return all(math.isfinite(c.real) and math.isfinite(c.imag)
               for c in field)


def rand_field(n, rng):
    """Haar-random unit complex field (an out-of-library probe)."""
    return normalize(
        [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]
    )


def noisy(field, sigma, rng):
    """Add i.i.d. complex Gaussian noise (std sigma per real part and
    per imaginary part, absolute, not relative to the field) and
    renormalise. The input list is not modified."""
    return normalize(
        [c + complex(rng.gauss(0, sigma), rng.gauss(0, sigma))
         for c in field]
    )


def phase_scrambled_field(n, seed):
    """Unit-magnitude field with i.i.d. uniform phases (seeded)."""
    rng = random.Random(seed)
    return normalize([
        complex(math.cos(a), math.sin(a))
        for a in (rng.uniform(0, 2 * math.pi) for _ in range(n))
    ])


def legacy_scrambled_field(n, seed):
    """v0.1.0 behaviour: cos and sin drawn from different angles."""
    rng = random.Random(seed)
    return normalize([
        complex(math.cos(rng.uniform(0, 2 * math.pi)),
                math.sin(rng.uniform(0, 2 * math.pi)))
        for _ in range(n)
    ])


TAU_STRATEGIES = ("midpoint", "first", "midpoint_all", "median")


def calibrate_tau(in_scores, ood_scores, grid=101, strategy="midpoint"):
    """Choose a gate threshold from calibration scores. Returns (tau, J).

    Accept rule is ``score >= tau`` (the gate rejects ``score < tau``).
    J = TPR - FPR (Youden) is evaluated on tau = i/grid, i = 0..grid.
    Among the taus with maximal J (ties within 1e-12):

    - "midpoint" (default): midpoint of the LONGEST contiguous run of
      maximal-J grid points (first run wins ties). This keeps tau
      inside a real plateau when maximal-J points are split.
    - "midpoint_all": midpoint of the first and last maximal-J tau,
      the v0.1.0 rule; it can fall outside the plateau if the
      maximal-J points are not contiguous.
    - "first": the first (lowest) maximal-J tau.
    - "median": the median maximal-J tau.
    """
    if strategy not in TAU_STRATEGIES:
        raise ValueError(f"strategy must be one of {TAU_STRATEGIES}")
    in_scores = list(in_scores)
    ood_scores = list(ood_scores)
    if not in_scores or not ood_scores:
        raise ValueError("calibration needs in-library and "
                         "out-of-library probes")
    if grid < 1:
        raise ValueError("grid must be at least 1")
    if not all(math.isfinite(v) for v in in_scores + ood_scores):
        raise ValueError("calibration scores must be finite")
    best_j, best_idx = -2.0, []
    for step in range(grid + 1):
        tau = step / grid
        tpr = sum(1 for v in in_scores if v >= tau) / len(in_scores)
        fpr = sum(1 for v in ood_scores if v >= tau) / len(ood_scores)
        j = tpr - fpr
        if j > best_j + 1e-12:
            best_j, best_idx = j, [step]
        elif abs(j - best_j) <= 1e-12:
            best_idx.append(step)
    if strategy == "first":
        step = best_idx[0]
        return step / grid, best_j
    if strategy == "midpoint_all":
        return (best_idx[0] + best_idx[-1]) / (2.0 * grid), best_j
    if strategy == "median":
        m = len(best_idx)
        mid = (best_idx[m // 2] + best_idx[(m - 1) // 2]) / 2.0
        return mid / grid, best_j
    runs, run = [], [best_idx[0]]
    for step in best_idx[1:]:
        if step == run[-1] + 1:
            run.append(step)
        else:
            runs.append(run)
            run = [step]
    runs.append(run)
    longest = max(runs, key=len)  # max keeps the first of equal lengths
    return (longest[0] + longest[-1]) / (2.0 * grid), best_j


class MembraneHeart:
    """Travelling-wave heart + holographic membrane + refusal gate.

    ``n_phases`` snapshots at t = i * period / n_phases are stored.
    ``envelope=False`` stores pure phase waves (the documented failure
    case: snapshots then differ only by a global phase).
    A gate that has not been calibrated (``tau is None``) refuses
    everything in :meth:`decide` (fail closed); use :meth:`classify`
    for ungated projection.
    """

    PHASE_NAMES = ("rest", "atrial", "ventricular", "recovery")

    def __init__(self, n=64, seed=42, period=40.0, width=8.0,
                 n_phases=4, k=4, envelope=True,
                 pacemaker_xy=(0.0, 5.0)):
        if period <= 0 or not math.isfinite(period):
            raise ValueError("period must be positive and finite")
        if width <= 0 or not math.isfinite(width):
            raise ValueError("width must be positive and finite")
        if n_phases < 2:
            raise ValueError("n_phases must be at least 2")
        self.geometry = HeartGeometry(n=n, seed=seed, k=k,
                                      pacemaker_xy=pacemaker_xy)
        self.n = n
        self.period = float(period)
        self.width = float(width)
        self.envelope = bool(envelope)
        self.n_phases = n_phases
        self.delays = self.geometry.delays
        if n_phases == len(self.PHASE_NAMES):
            self.phase_names = self.PHASE_NAMES
        else:
            self.phase_names = tuple(f"phase_{i}" for i in range(n_phases))
        self.phase_times = tuple(i * self.period / n_phases
                                 for i in range(n_phases))
        self.patterns = [self.field(t) for t in self.phase_times]
        self.tau = None

    def field(self, t, width=None):
        """Enveloped travelling-wave field at time t, unit length.

        With ``envelope=False`` the amplitude is 1 for every neuron.
        """
        w = self.width if width is None else width
        out = []
        for d in self.delays:
            s = (t - d) % self.period
            amp = (math.exp(-(s * s) / (2.0 * w * w))
                   if self.envelope else 1.0)
            phase = 2.0 * math.pi * (t - d) / self.period
            out.append(amp * complex(math.cos(phase), math.sin(phase)))
        return normalize(out)

    def _check_length(self, field):
        if len(field) != self.n:
            raise ValueError(
                f"field has {len(field)} entries, expected {self.n}")

    def coherence(self, field, t):
        """1.0 = field follows the wave exactly; ~0.125 = random."""
        self._check_length(field)
        return abs(overlap(field, self.field(t)))

    def overlaps(self, field):
        self._check_length(field)
        return [overlap(field, p) for p in self.patterns]

    def project(self, field):
        """(winner index or None, probabilities).

        None for a zero or non-finite field. Exact ties go to the
        lowest index (documented; see DESIGN.md for why that matters
        for pure-phase storage).
        """
        ms = self.overlaps(field)
        if not is_finite_field(ms):
            return None, [0.0] * len(ms)
        tot = math.fsum(abs(m) ** 2 for m in ms)
        if tot == 0:
            return None, [0.0] * len(ms)
        probs = [abs(m) ** 2 / tot for m in ms]
        return max(range(len(ms)), key=lambda i: abs(ms[i])), probs

    def max_overlap(self, field):
        ms = self.overlaps(field)
        if not is_finite_field(ms):
            return float("nan")
        return max(abs(m) for m in ms)

    def classify(self, field):
        """Ungated projection: phase name or None. No refusal."""
        winner, _ = self.project(field)
        return None if winner is None else self.phase_names[winner]

    def calibrate(self, in_probes, ood_probes, grid=101,
                  strategy="midpoint"):
        """Freeze tau from calibration probes. Returns (tau, J).

        Calibration probes must be disjoint from evaluation probes;
        this method cannot check that, so experiments derive separate
        seeds (see membrane_heart.stats.derive_seed).
        """
        in_max = [self.max_overlap(f) for f in in_probes]
        ood_max = [self.max_overlap(f) for f in ood_probes]
        tau, j = calibrate_tau(in_max, ood_max, grid, strategy)
        self.tau = tau
        return tau, j

    def decide(self, field):
        """('accept', phase_name, probs) or ('reject', None, probs).

        Fail closed: an uncalibrated gate, a zero field, or a
        non-finite field is rejected. A field of the wrong length
        raises ValueError. ``max_overlap == tau`` is accepted.
        """
        winner, probs = self.project(field)
        if winner is None or self.tau is None:
            return "reject", None, probs
        if self.max_overlap(field) < self.tau:
            return "reject", None, probs
        return "accept", self.phase_names[winner], probs

    def scrambled_field(self, seed):
        """A broken beat: unit magnitudes, uniformly random phases.

        The wave no longer travels, so coherence collapses and the
        gate should refuse it. This is a SYNTHETIC out-of-library
        field, not a model of any condition.
        """
        return phase_scrambled_field(self.n, seed)

    def legacy_scrambled_field(self, seed):
        """The v0.1.0 generator as supplied (kept for reproduction).

        It draws two independent angles per neuron (one for the real
        part, one for the imaginary part), so magnitudes are NOT unit
        despite the v0.1.0 description. See DESIGN.md.
        """
        return legacy_scrambled_field(self.n, seed)

    def pattern_gram(self):
        """|<p_i, p_j>| matrix of the stored patterns."""
        return [[abs(overlap(pj, pi)) for pj in self.patterns]
                for pi in self.patterns]

    def max_neighbour_overlap(self):
        """Largest |<p_i, p_{i+1 mod n_phases}>| (cyclic neighbours)."""
        g = self.pattern_gram()
        m = self.n_phases
        return max(g[i][(i + 1) % m] for i in range(m))
