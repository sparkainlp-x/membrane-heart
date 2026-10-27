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
    n = math.sqrt(sum(abs(c) ** 2 for c in v))
    if n == 0:
        raise ValueError("cannot normalize a zero vector")
    return [c / n for c in v]


def overlap(field, pattern):
    return sum(p.conjugate() * f for p, f in zip(pattern, field))


def rand_field(n, rng):
    """Haar-random unit complex field (an out-of-library probe)."""
    return normalize(
        [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]
    )


def noisy(field, sigma, rng):
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


class MembraneHeart:
    """Travelling-wave heart + holographic membrane + refusal gate."""

    PHASE_NAMES = ("rest", "atrial", "ventricular", "recovery")

    def __init__(self, n=64, seed=42, period=40.0):
        if period <= 0:
            raise ValueError("period must be positive")
        self.geometry = HeartGeometry(n=n, seed=seed)
        self.n = n
        self.period = period
        self.delays = self.geometry.delays
        # Four stored beat phases, as unit complex fields.
        self.patterns = [
            self.field(t) for t in (0.0, period / 4, period / 2,
                                    3 * period / 4)
        ]
        self.tau = None

    def field(self, t, width=8.0):
        """Enveloped travelling-wave field at time t, unit length."""
        out = []
        for d in self.delays:
            s = (t - d) % self.period
            amp = math.exp(-(s * s) / (2.0 * width * width))
            phase = 2.0 * math.pi * (t - d) / self.period
            out.append(amp * complex(math.cos(phase), math.sin(phase)))
        return normalize(out)

    def coherence(self, field, t):
        """1.0 = field follows the wave exactly; ~0.125 = random."""
        return abs(overlap(field, self.field(t)))

    def overlaps(self, field):
        return [overlap(field, p) for p in self.patterns]

    def project(self, field):
        ms = self.overlaps(field)
        tot = sum(abs(m) ** 2 for m in ms)
        if tot == 0:
            return None, [0.0] * len(ms)
        probs = [abs(m) ** 2 / tot for m in ms]
        return max(range(len(ms)), key=lambda i: abs(ms[i])), probs

    def max_overlap(self, field):
        return max(abs(m) for m in self.overlaps(field))

    def calibrate(self, in_probes, ood_probes, grid=101):
        """Freeze tau: midpoint of the taus maximising Youden's J."""
        in_max = [self.max_overlap(f) for f in in_probes]
        ood_max = [self.max_overlap(f) for f in ood_probes]
        best_j, best_taus = -2.0, []
        for step in range(grid + 1):
            tau = step / grid
            tpr = sum(1 for v in in_max if v >= tau) / len(in_max)
            fpr = sum(1 for v in ood_max if v >= tau) / len(ood_max)
            j = tpr - fpr
            if j > best_j + 1e-12:
                best_j, best_taus = j, [tau]
            elif abs(j - best_j) <= 1e-12:
                best_taus.append(tau)
        self.tau = (best_taus[0] + best_taus[-1]) / 2.0
        return self.tau, best_j

    def decide(self, field):
        """('accept', phase_name, probs) or ('reject', None, probs)."""
        winner, probs = self.project(field)
        if winner is None:
            return "reject", None, probs
        if self.tau is not None and self.max_overlap(field) < self.tau:
            return "reject", None, probs
        return "accept", self.PHASE_NAMES[winner], probs

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
