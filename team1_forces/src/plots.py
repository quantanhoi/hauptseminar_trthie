"""Gemeinsame Plot-Helfer: einheitlicher Stil, deutschsprachige Beschriftung
(die Labels selbst setzt jedes Notebook), Speichern unter figures/."""

from pathlib import Path

import matplotlib.pyplot as plt

# Projektwurzel = parents[1] dieser Datei (team1_forces/src/plots.py -> team1_forces/)
FIGURES_DIR = Path(__file__).resolve().parents[1] / "figures"


def setup_style():
    """Setzt den gemeinsamen Stil für alle Notebooks."""
    plt.rcParams.update({
        "figure.figsize": (7, 4.5),
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "font.size": 11,
        "axes.grid": True,
        "grid.alpha": 0.3,
    })


def save_fig(fig, name):
    """Speichert die Abbildung als PNG unter figures/ und gibt den Pfad zurück."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, bbox_inches="tight")
    return path