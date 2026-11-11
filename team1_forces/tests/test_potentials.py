import numpy as np
import pytest

from src.constants import kB, T_REF, NM, PN, DEBYE_LENGTHS, kBT
from src.potentials import ProtocellForces


def test_constants_values():
    assert kB == 1.380649e-23
    assert T_REF == 298.15
    assert NM == 1e-9
    assert PN == 1e-12
    assert DEBYE_LENGTHS == {50: 1.36e-9, 100: 0.96e-9, 200: 0.68e-9}
    assert kBT() == kB * T_REF
    assert kBT(300.0) == kB * 300.0


@pytest.fixture
def model():
    return ProtocellForces()


def test_force_is_negative_gradient_of_potential(model):
    # Uniform grid so the central difference is valid; starts at 1 nm where
    # the central-diff truncation on the L^-12 core stays < 2% (ledger ruling).
    L = np.linspace(1e-9, 100e-9, 4001)
    dL = L[1] - L[0]
    pairs = [
        (model.U_vdw, model.F_vdw),
        (model.U_el, model.F_el),
        (model.U_core, model.F_core),
        (model.U_dlvo, model.F_dlvo),
    ]
    for U, F in pairs:
        numeric = -(U(L)[2:] - U(L)[:-2]) / (2 * dL)
        assert np.allclose(F(L)[1:-1], numeric, rtol=5e-2), U.__name__

    # CL potential is only defined via numeric integration of F = -dU/dL.
    U_cl = model.U_cl_retarded_numeric(L)
    numeric = -(U_cl[2:] - U_cl[:-2]) / (2 * dL)
    assert np.allclose(model.F_cl_retarded(L)[1:-1], numeric, rtol=5e-2)


def test_retardation_factor_bounds(model):
    assert np.isclose(model.retardation_factor(5e-9), 1.0 / 1.25**2, rtol=1e-6)
    assert np.isclose(model.retardation_factor(20e-9), 0.25, rtol=1e-6)
    grid = np.geomspace(0.2e-9, 100e-9, 300)
    r = model.retardation_factor(grid)
    assert np.all(r <= 1.0)
    assert np.all(np.diff(r) < 0)  # strictly decreasing on ascending grid


def test_clip_floors_small_L(model):
    assert model.U_vdw(1e-15) == model.U_vdw(0.2e-9)


def test_accepts_scalar_and_array(model):
    scalar = model.F_vdw(10e-9)
    assert np.isscalar(scalar) or isinstance(scalar, np.floating)
    arr = model.F_vdw(np.array([2e-9, 5e-9]))
    assert arr.shape == (2,)


def test_mode_separation(model):
    # Im elektrostatisch relevanten Bereich (2–6 nm) müssen DLVO und der
    # retardierte vdW-Grenzfall unterscheidbar sein. Bei großen L konvergieren
    # beide zulässig gegen ~0 (El/Core verschwinden), deshalb kleiner Bereich
    # und ein atol, das die Größenordnung von Pikonewton ernst nimmt.
    L = np.linspace(2e-9, 6e-9, 41)
    combined = model.F_vdw(L) * model.retardation_factor(L)
    assert not np.allclose(model.F_dlvo(L), combined, rtol=1e-3, atol=1e-15)