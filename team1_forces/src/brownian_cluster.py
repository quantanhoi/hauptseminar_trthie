"""2D-Mehrteilchen-Brownian-Dynamik mit periodischen Randbedingungen (§12).

Vektorisierte Version der Anhangs-Doppelschleife (identische Mathematik),
ergänzt um Kraftbegrenzung (§18 Fehler 6) und Gitter-Startbedingungen.
"""

import numpy as np

from src.pair_dynamics import contact_zone


class BrownianClusterSim:
    def __init__(
        self,
        n=20,
        R=500e-9,
        box=20e-6,
        dt=1e-4,
        mobility=1e8,
        diffusion=1e-16,
        seed=0,
        force_cap=None,
        x=None,
    ):
        self.rng = np.random.default_rng(seed)
        self.R = R
        self.box = box
        self.dt = dt
        self.mobility = mobility
        self.diffusion = diffusion
        self.force_cap = force_cap
        if x is not None:
            self.x = np.asarray(x, dtype=float).copy()
            self.n = len(self.x)
        else:
            self.n = n
            self.x = self.rng.uniform(0, box, size=(n, 2))

    def minimum_image(self, delta):
        return delta - self.box * np.round(delta / self.box)

    def step(self, force_model, mode="dlvo"):
        if mode == "dlvo":
            force = force_model.F_dlvo
        elif mode == "vdw":
            force = force_model.F_vdw
        elif mode == "cl_retarded":
            force = force_model.F_cl_retarded
        else:
            raise ValueError("unknown mode")

        # delta[i, j] = x[j] - x[i] (Minimum-Image), alles paarmatrixweise.
        delta = self.minimum_image(self.x[None, :, :] - self.x[:, None, :])
        dist = np.linalg.norm(delta, axis=-1) + 1e-30
        L = np.maximum(dist - 2 * self.R, 0.2e-9)
        F = np.asarray(force(L), dtype=float)
        if self.force_cap is not None:
            F = np.clip(F, -self.force_cap, self.force_cap)
        np.fill_diagonal(F, 0.0)  # Selbstwechselwirkung: Richtung ist exakt 0
        direction = delta / dist[..., None]
        # §5-Vorzeichenkonvention: F < 0 wirkt anziehend. Die physikalische
        # Kraft auf Partikel i ist -F * u_ij (u_ij zeigt von i zu j) — der
        # Anhang verwendet hier += F*direction und kehrt damit Anziehung und
        # Abstoßung gegeneinander um (Korrektur, siehe report/Grenzen).
        forces = np.sum(-F[..., None] * direction, axis=1)
        if self.force_cap is not None:
            # Stabilitätsregel gilt pro Partikel: auch die Summe über Nachbarn
            # wird auf force_cap begrenzt (Verhinderung von Box-Sprüngen).
            norms = np.linalg.norm(forces, axis=1, keepdims=True)
            forces = forces * np.minimum(1.0, self.force_cap / np.maximum(norms, 1e-30))
        noise = np.sqrt(2 * self.diffusion * self.dt) * self.rng.normal(size=self.x.shape)
        self.x += self.mobility * forces * self.dt + noise
        self.x = np.mod(self.x, self.box)
        return self.x

    def pair_distance_table(self):
        rows = []
        for i in range(self.n):
            for j in range(i + 1, self.n):
                delta = self.minimum_image(self.x[j] - self.x[i])
                dist = np.linalg.norm(delta)
                L = max(dist - 2 * self.R, 0.2e-9)  # Floor konsistent mit step()
                rows.append((i, j, L, contact_zone(L)))
        return rows


def lattice_positions(n, box, R, gap, seed=0):
    """Vorgeclusterter Start: quadratisches Gitter, Gitterkonstante 2R + gap,
    zentriert in der Box, Jitter ±10 % von gap pro Koordinate.

    shortcut: Jitter relativ zu gap (nicht zur Gitterkonstante), weil gap nur
    ~2 % der Gitterkonstante ist und spacing-Jitter Überlappungen erlauben würde.
    """
    rng = np.random.default_rng(seed)
    side = int(np.ceil(np.sqrt(n)))
    a = 2 * R + gap
    idx = np.arange(n)
    pts = np.column_stack([(idx % side) * a, (idx // side) * a])
    pts += (box - (side - 1) * a) / 2.0
    pts += rng.uniform(-0.1 * gap, 0.1 * gap, size=pts.shape)
    return pts