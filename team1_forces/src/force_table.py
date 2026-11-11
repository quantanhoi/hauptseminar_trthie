"""Krafttabellen an Stützstellen (Aufgabenblatt §12)."""

import pandas as pd

from src.constants import PN, kBT
from src.potentials import ProtocellForces


def force_table(model, L_nm_values=(2, 3, 5, 10, 20, 30, 50, 100)):
    rows = []
    for L_nm in L_nm_values:
        L = L_nm * 1e-9
        rows.append(
            {
                "L_nm": L_nm,
                "F_vdw_pN": model.F_vdw(L) / PN,
                "F_el_pN": model.F_el(L) / PN,
                "F_dlvo_pN": model.F_dlvo(L) / PN,
                "F_cl_ret_pN": model.F_cl_retarded(L) / PN,
                # U/kBT mit der Modelltemperatur normieren (nicht T_REF)
                "U_vdw_kBT": model.U_vdw(L) / kBT(model.T),
                "U_dlvo_kBT": model.U_dlvo(L) / kBT(model.T),
                "retardation_factor": model.retardation_factor(L),
            }
        )
    return pd.DataFrame(rows)