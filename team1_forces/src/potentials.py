"""Kraft-/Potentialmodelle für Protozellen (vdW, DLVO, CL-retarded).

Die vier Modellmodi bleiben streng getrennt (§3): F_dlvo enthält Elektrostatik,
vdW und Core; F_cl_retarded ist der vdW-Grenzfall mit Retardierungsfaktor.
vdW und CL werden nie addiert (§18 Fehler 1).
"""

import numpy as np

from src.constants import kB, T_REF


class ProtocellForces:
    def __init__(
        self,
        R=500e-9,
        A_H=1e-21,
        lambda_D=0.96e-9,
        B_kBT=20.0,
        T=T_REF,
        L_core=0.5e-9,
        C_core_kBT=0.5,
        L_ret=20e-9,
        p_ret=2,
        L_min=0.2e-9,
    ):
        self.R = R
        self.R_eff = R / 2.0
        self.A_H = A_H
        self.lambda_D = lambda_D
        self.kappa = 1.0 / lambda_D
        self.T = T
        self.B = B_kBT * kB * T
        self.L_core = L_core
        self.C_core = C_core_kBT * kB * T
        self.L_ret = L_ret
        self.p_ret = p_ret
        self.L_min = L_min

    def clip(self, L):
        return np.maximum(L, self.L_min)

    def U_vdw(self, L):
        L = self.clip(L)
        return -self.A_H * self.R_eff / (6.0 * L)

    def F_vdw(self, L):
        L = self.clip(L)
        return -self.A_H * self.R_eff / (6.0 * L**2)

    def U_el(self, L):
        L = self.clip(L)
        return self.B * np.exp(-self.kappa * L)

    def F_el(self, L):
        L = self.clip(L)
        return self.kappa * self.U_el(L)

    def U_core(self, L):
        L = self.clip(L)
        return self.C_core * (self.L_core / L) ** 12

    def F_core(self, L):
        L = self.clip(L)
        return 12.0 * self.C_core * self.L_core**12 / L**13

    def U_dlvo(self, L):
        return self.U_el(L) + self.U_vdw(L) + self.U_core(L)

    def F_dlvo(self, L):
        return self.F_el(L) + self.F_vdw(L) + self.F_core(L)

    def retardation_factor(self, L):
        L = self.clip(L)
        return 1.0 / (1.0 + L / self.L_ret) ** self.p_ret

    def F_cl_retarded(self, L):
        return self.F_vdw(L) * self.retardation_factor(L)

    def U_cl_retarded_numeric(self, L_grid):
        """Numerische Integration aus F = -dU/dL (didaktisch, §12).

        U(L_max) = 0 und Rückwärtsintegration (Trapez) über ein aufsteigendes Gitter.
        """
        L = np.asarray(L_grid, dtype=float)
        if not np.all(np.diff(L) > 0):
            raise ValueError("L_grid muss streng aufsteigend sein")
        F = self.F_cl_retarded(L)
        U = np.zeros_like(L)
        for i in range(len(L) - 2, -1, -1):
            dL = L[i + 1] - L[i]
            U[i] = U[i + 1] - 0.5 * (F[i + 1] + F[i]) * dL
        return U