"""Gemeinsamer Plot-Stil; inhaltliche deutsche Labels setzen die Notebooks."""

from pathlib import Path

import matplotlib.pyplot as plt

FIGURES_DIR = Path(__file__).resolve().parents[1] / "figures"


def setup_style():
    plt.rcParams.update({
        "figure.figsize": (7, 4.5),
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.25,
    })


def save_fig(fig, name, out_dir=FIGURES_DIR):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    return path
