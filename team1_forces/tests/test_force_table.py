import numpy as np
import pandas as pd
import pytest

from src.constants import kB, T_REF, PN
from src.potentials import ProtocellForces
from src.force_table import force_table

EXPECTED_COLUMNS = [
    "L_nm",
    "F_vdw_pN",
    "F_el_pN",
    "F_dlvo_pN",
    "F_cl_ret_pN",
    "U_vdw_kBT",
    "U_dlvo_kBT",
    "retardation_factor",
]


def test_columns_and_index():
    df = force_table(ProtocellForces())
    assert list(df.columns) == EXPECTED_COLUMNS
    assert list(df["L_nm"]) == [2, 3, 5, 10, 20, 30, 50, 100]


def test_known_value():
    model = ProtocellForces(A_H=5e-21)
    df = force_table(model)
    expected = -5e-21 * 250e-9 / (6 * (100e-9) ** 2) / PN  # F_vdw(100 nm) in pN
    got = df.loc[df.L_nm == 100, "F_vdw_pN"].item()
    assert np.isclose(got, expected, rtol=1e-3)


def test_dlvo_equals_vdw_at_large_L():
    # Bei 100 nm sind Elektrostatik (Debye) und Core vernachlässigbar;
    # F_dlvo muss dort im Wesentlichen F_vdw folgen.
    df = force_table(ProtocellForces(A_H=5e-21))
    row = df.loc[df.L_nm == 100].iloc[0]
    assert np.isclose(row["F_dlvo_pN"], row["F_vdw_pN"], rtol=1e-2)


def test_kbt_uses_model_temperature():
    # U/kBT muss mit der Temperatur des MODELLS normiert werden, nicht mit T_REF.
    model = ProtocellForces(A_H=5e-21, T=1000.0)
    df = force_table(model)
    expected = model.U_vdw(10e-9) / (kB * 1000.0)
    got = df.loc[df.L_nm == 10, "U_vdw_kBT"].item()
    assert np.isclose(got, expected, rtol=1e-9)