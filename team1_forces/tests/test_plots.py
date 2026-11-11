import matplotlib

matplotlib.use("Agg")  # tesweise ohne Display

import matplotlib.pyplot as plt

from src.plots import setup_style, save_fig


def test_save_fig(tmp_path, monkeypatch):
    import src.plots as plots

    monkeypatch.setattr(plots, "FIGURES_DIR", tmp_path)
    setup_style()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    path = save_fig(fig, "smoke")
    assert path.exists()
    assert path.name == "smoke.png"