import numpy as np
import pytest

from src.potentials import ProtocellForces
from src.pair_dynamics import PairBrownian1D, contact_zone


def test_zone_boundaries():
    cases = [
        (1.9e-9, "hard_contact"),
        (2e-9, "dlvo_zone"),
        (4.9e-9, "dlvo_zone"),
        (5e-9, "near_gap"),
        (9.9e-9, "near_gap"),
        (10e-9, "meso_gap"),
        (29e-9, "meso_gap"),
        (30e-9, "far_gap"),
        (99e-9, "far_gap"),
        (100e-9, "separated"),
    ]
    for L, expected in cases:
        assert contact_zone(L) == expected, L


def test_seed_reproducibility():
    model = ProtocellForces(A_H=5e-21)
    a = PairBrownian1D(model, seed=7, dt=1e-7, force_cap=20e-12).run(500)
    b = PairBrownian1D(model, seed=7, dt=1e-7, force_cap=20e-12).run(500)
    assert np.array_equal(a, b)


def test_force_cap_bounds_drift():
    model = ProtocellForces(B_kBT=1e9)  # enorme Abstoßung
    sim = PairBrownian1D(model, L0=1e-9, dt=1e-7, force_cap=20e-12)
    prev = sim.L
    noise_sigma = np.sqrt(2 * sim.diffusion * sim.dt)
    drift_bound = sim.mobility * 20e-12 * sim.dt
    for _ in range(200):
        L = sim.step()
        assert np.isfinite(L)
        assert abs(L - prev) <= drift_bound + 6 * noise_sigma
        prev = L


def test_clamp():
    model = ProtocellForces(B_kBT=1e9)
    sim = PairBrownian1D(model, L0=1e-9)  # dt=1e-4, ohne Cap: Drift >> Box
    traj = sim.run(10)
    assert np.all(traj >= sim.L_min)
    assert np.all(traj <= sim.L_max)
    assert np.all(np.isfinite(traj))


def test_unknown_mode_raises():
    sim = PairBrownian1D(ProtocellForces())
    with pytest.raises(ValueError):
        sim.step(mode="bogus")