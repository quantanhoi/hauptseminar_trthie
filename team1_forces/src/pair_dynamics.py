"""1D-Brownian-Dynamik des Oberflächenabstands L eines Paares (§12),
erweitert um Kraftbegrenzung (§18 Fehler 6)."""

import numpy as np


class PairBrownian1D:
    def __init__(
        self,
        force_model,
        L0=20e-9,
        dt=1e-4,
        mobility=1e8,
        diffusion=1e-16,
        L_min=0.5e-9,
        L_max=200e-9,
        seed=0,
        force_cap=None,
    ):
        self.force_model = force_model
        self.L = L0
        self.dt = dt
        self.mobility = mobility
        self.diffusion = diffusion
        self.L_min = L_min
        self.L_max = L_max
        self.force_cap = force_cap
        self.rng = np.random.default_rng(seed)

    def _force(self, mode):
        if mode == "dlvo":
            F = self.force_model.F_dlvo(self.L)
        elif mode == "vdw":
            F = self.force_model.F_vdw(self.L)
        elif mode == "cl_retarded":
            F = self.force_model.F_cl_retarded(self.L)
        else:
            raise ValueError("unknown mode")
        if self.force_cap is not None:
            F = np.clip(F, -self.force_cap, self.force_cap)
        return F

    def step(self, mode="dlvo"):
        F = self._force(mode)
        drift = self.mobility * F * self.dt
        noise = np.sqrt(2 * self.diffusion * self.dt) * self.rng.normal()
        self.L = self.L + drift + noise
        self.L = min(max(self.L, self.L_min), self.L_max)
        return self.L

    def run(self, steps=10000, mode="dlvo"):
        traj = np.zeros(steps)
        for t in range(steps):
            traj[t] = self.step(mode=mode)
        return traj


def contact_zone(L):
    if L < 2e-9:
        return "hard_contact"
    if L < 5e-9:
        return "dlvo_zone"
    if L < 10e-9:
        return "near_gap"
    if L < 30e-9:
        return "meso_gap"
    if L < 100e-9:
        return "far_gap"
    return "separated"