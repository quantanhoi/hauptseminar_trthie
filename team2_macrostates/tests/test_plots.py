import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.plots import save_fig, setup_style


def test_shared_style_and_png_save(tmp_path):
    setup_style()
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="gefiltert")
    ax.set_xlabel("Zeit (s)")
    ax.set_ylabel("Makrozustand")
    assert ax.get_xlabel() == "Zeit (s)"
    assert ax.get_ylabel() == "Makrozustand"
    assert ax.lines
    assert plt.rcParams["savefig.dpi"] == 200

    path = save_fig(fig, "test_plot", out_dir=tmp_path)
    assert path.name == "test_plot.png"
    assert path.stat().st_size > 1000
    image = plt.imread(path)
    assert image.size > 0
    plt.close(fig)
