import numpy as np
import pytest

from src.potentials import ProtocellForces
from src.brownian_cluster import BrownianClusterSim, lattice_positions

MODE_METHOD = {
    "dlvo": "F_dlvo",
    "vdw": "F_vdw",
    "cl_retarded": "F_cl_retarded",
}


def naive_step(sim, model, mode):
    """Referenzimplementierung des Anhangs (Doppelschleife, i<j, Newtons drittes
    Gesetz), mit korrigierter Vorzeichenkonvention (§5: F < 0 anziehend)."""
    method = getattr(model, MODE_METHOD[mode])
    forces = np.zeros_like(sim.x)
    for i in range(sim.n):
        for j in range(i + 1, sim.n):
            delta = sim.minimum_image(sim.x[j] - sim.x[i])
            dist = np.linalg.norm(delta) + 1e-30
            L = max(dist - 2 * sim.R, 0.2e-9)
            direction = delta / dist
            F = method(L)
            if sim.force_cap is not None:
                F = np.clip(F, -sim.force_cap, sim.force_cap)
            forces[i] -= F * direction
            forces[j] += F * direction
    if sim.force_cap is not None:
        # identische Netto-Kraftbegrenzung pro Partikel wie die Vektorisierung
        norms = np.linalg.norm(forces, axis=1, keepdims=True)
        forces = forces * np.minimum(1.0, sim.force_cap / np.maximum(norms, 1e-30))
    noise = np.sqrt(2 * sim.diffusion * sim.dt) * sim.rng.normal(size=sim.x.shape)
    x = sim.x + sim.mobility * forces * sim.dt + noise
    return np.mod(x, sim.box)


@pytest.mark.parametrize("mode", ["dlvo", "vdw", "cl_retarded"])
def test_matches_loop_reference(mode):
    model = ProtocellForces(A_H=5e-21)
    kwargs = dict(n=3, R=500e-9, box=2e-6, dt=1e-7, seed=3, force_cap=20e-12)
    a = BrownianClusterSim(**kwargs)
    b = BrownianClusterSim(**kwargs)
    x_ref = naive_step(b, model, mode)
    x_vec = a.step(model, mode=mode)
    assert np.allclose(x_vec, x_ref, atol=1e-18)
    assert np.array_equal(x_vec, x_ref) or np.allclose(x_vec, x_ref, atol=1e-22)


def test_overlap_is_floored():
    model = ProtocellForces(A_H=5e-21)
    x = np.array([[5e-6, 5e-6], [5e-6 + 1e-9, 5e-6]])  # dist << 2R, im Box-Inneren
    sim = BrownianClusterSim(n=2, x=x, dt=1e-7, seed=0, force_cap=20e-12)
    old = sim.x.copy()
    new = sim.step(model, mode="dlvo")
    assert np.all(np.isfinite(new))
    bound = sim.mobility * 20e-12 * sim.dt + 6 * np.sqrt(2 * sim.diffusion * sim.dt)
    assert np.all(np.abs(new - old) <= bound)


def test_minimum_image():
    sim = BrownianClusterSim(n=2, box=20e-6)
    out = sim.minimum_image(np.array([19e-6, 0.0]))
    assert np.allclose(out, [-1e-6, 0.0])


def test_pair_distance_table_zones():
    x = np.array(
        [
            [0.0, 0.0],
            [2 * 500e-9 + 3e-9, 0.0],          # L = 3 nm -> dlvo_zone
            [10e-6, 10e-6],
            [10e-6 + 2 * 500e-9 + 150e-9, 10e-6],  # L = 150 nm -> separated
        ]
    )
    sim = BrownianClusterSim(n=4, x=x, box=20e-6)
    rows = sim.pair_distance_table()
    by_pair = {(i, j): (L, zone) for i, j, L, zone in rows}
    L, zone = by_pair[(0, 1)]
    assert np.isclose(L, 3e-9)
    assert zone == "dlvo_zone"
    assert by_pair[(2, 3)][1] == "separated"


def test_lattice_positions():
    x = lattice_positions(n=20, box=20e-6, R=500e-9, gap=20e-9, seed=0)
    assert x.shape == (20, 2)
    assert np.all(x >= 0) and np.all(x <= 20e-6)
    dists = np.linalg.norm(x[:, None, :] - x[None, :, :], axis=-1)
    dists = dists[dists > 0]
    assert np.all(dists >= 2 * 500e-9)  # keine Überlappung
    assert np.array_equal(x, lattice_positions(n=20, box=20e-6, R=500e-9, gap=20e-9, seed=0))


def test_seed_reproducibility():
    model = ProtocellForces(A_H=5e-21)
    kwargs = dict(n=5, R=500e-9, box=3e-6, dt=1e-7, seed=11, force_cap=20e-12)
    a = BrownianClusterSim(**kwargs)
    b = BrownianClusterSim(**kwargs)
    for _ in range(50):
        a.step(model, mode="dlvo")
        b.step(model, mode="dlvo")
    assert np.array_equal(a.x, b.x)


def test_unknown_mode_raises():
    sim = BrownianClusterSim(n=2)
    with pytest.raises(ValueError):
        sim.step(ProtocellForces(), mode="bogus")


def test_attraction_closes_gap():
    # §5: F < 0 wirkt anziehend. Zwei Zellen im Abstand L = 20 nm unter reiner
    # vdW-Anziehung müssen sich ANNÄHERN (Abstand sinkt), nicht entfernen.
    # Fängt den Vorzeichenfehler des Anhangs (forces[i] += F*direction) ab.
    model = ProtocellForces(A_H=5e-21, B_kBT=0.0, C_core_kBT=0.0)
    x0 = np.array([[5e-6, 5e-6], [5e-6 + 2 * 500e-9 + 20e-9, 5e-6]])
    sim = BrownianClusterSim(n=2, x=x0, dt=1e-7, seed=0, force_cap=20e-12)
    d0 = np.linalg.norm(sim.x[1] - sim.x[0])
    for _ in range(2000):
        sim.step(model, mode="vdw")
    d1 = np.linalg.norm(sim.x[1] - sim.x[0])
    assert d1 < d0


def test_pair_table_floors_overlapping_gap():
    # Konsistent mit der Wechselwirkungs-Floor in step(): überlappende Paare
    # bekommen L = 0.2 nm, nicht 0.0 (Team-2-Datenkonsistenz).
    x = np.array([[5e-6, 5e-6], [5e-6 + 1e-9, 5e-6]])
    sim = BrownianClusterSim(n=2, x=x)
    i, j, L, zone = sim.pair_distance_table()[0]
    assert L == 0.2e-9
    assert zone == "hard_contact"


def test_net_force_capped_multi_overlap():
    # Drei überlappende Partikel: auch die SUMMIerte Kraft pro Partikel bleibt
    # beim Cap (Stabilitätsregel gilt pro Partikel, nicht nur pro Paar).
    x = np.array([[5e-6, 5e-6], [5e-6 + 1e-9, 5e-6], [5e-6 + 2e-9, 5e-6]])
    sim = BrownianClusterSim(n=3, x=x, dt=1e-7, seed=0, force_cap=20e-12)
    model = ProtocellForces(A_H=5e-21)
    old = sim.x.copy()
    new = sim.step(model, mode="dlvo")
    bound = sim.mobility * 20e-12 * sim.dt + 6 * np.sqrt(2 * sim.diffusion * sim.dt)
    assert np.all(np.abs(new - old) <= bound)