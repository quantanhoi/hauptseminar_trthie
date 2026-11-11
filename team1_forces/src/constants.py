"""Physikalische Konstanten und Referenzwerte (Aufgabenblatt §12)."""

import numpy as np

kB = 1.380649e-23  # J/K
T_REF = 298.15     # K
NM = 1e-9
PN = 1e-12

DEBYE_LENGTHS = {
    50: 1.36e-9,
    100: 0.96e-9,
    200: 0.68e-9,
}


def kBT(T=T_REF):
    return kB * T