# Team 2 – Makrozustände, Abstandszonen und Attractor Memory

Reproduzierbare Pipeline für das Master-Seminar „Construction Theory of
Information und Software in the Natural World“. Sie verbindet die
mikrophysikalischen Team-1-Daten mit robusten Makrozuständen für Team 3:
physikalisch begründete Abstandszonen, mehrere Kontaktgraphen, Persistenzfilter,
Dwell/Return-Metriken, Jitter-Robustheit und ein sauberes Exportformat.

## Setup

Das Projekt verwendet denselben Python-3.12-Stack wie Team 1. Für die
Entwicklung wurde die vorhandene Umgebung verwendet:

```bash
cd team2_macrostates
../team1_forces/.venv/bin/python -m pytest -q
```

Für eine unabhängige Umgebung:

```bash
cd team2_macrostates
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Eingabedaten

 notebooks lesen `../team1_forces/data/processed/{positions.csv,parameters.csv}`.
Der finale Export enthält **19 Runs mit je 1000 Frames**: 18 vergleichbare
N=20-Läufe aus {`vdw`, `dlvo`, `cl_retarded`} × {PMBC `A_H = 5×10⁻²¹ J`,
Fettsäure `A_H = 0.5×10⁻²¹ J`} × Seeds {0, 1, 42}, plus ein getrennter
N=50-Lauf (`cl_retarded`/PMBC, Seed 42).

Erwartete Einheiten:

| Größe | Einheit |
|---|---|
| Positionen `x`, `y` | Meter |
| Zeit `t` / `time` | Sekunden |
| Oberflächenabstand `L_nm` | Nanometer |
| Radius `R_nm` | Nanometer |
| Hamaker-Konstante `A_H` | Joule |
| Periodische Box | fest 20 µm (`20e-6 m`) |

Nur zwei dokumentierte Materialwerte werden interpretiert:
`A_H = 0.5×10⁻²¹ J` ist `fatty_acid`, `A_H = 5×10⁻²¹ J` ist `PMBC`. Andere
Werte bleiben `unknown`. Es gibt **kein** `cl_meso_hypothesis`, weil dieses
Aufgabenblatt keinen Formel-/Parametervertrag dafür definiert.

## Notebooks ausführen

Reihenfolge beachten, weil Notebook 01 die Kern-CSVs erzeugt:

```bash
../team1_forces/.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=3600 notebooks/01_zones_graphs.ipynb
../team1_forces/.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=3600 notebooks/02_sequences_attractors.ipynb
../team1_forces/.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=3600 notebooks/03_robustness_comparison.ipynb
```

## Projektstruktur

```
team2_macrostates/
├── src/
│   ├── zones.py             # Oberflächenabstand und §6-Zonen
│   ├── contact_graphs.py    # Paare, Graphen und Graphfeatures
│   ├── macrostates.py       # kleiner regelbasierter Katalog
│   ├── sequences.py         # Filter, Dwell, Transition, Return
│   ├── robustness.py        # reproduzierbarer Jitter und Label Agreement
│   ├── pipeline.py          # Team-1-Laden, Validierung, Export
│   └── plots.py             # gemeinsamer Plot-Stil
├── notebooks/               # 01 Zonen/Graphen · 02 Persistenz · 03 Robustheit
├── data/processed/          # erzeugte Team-2-/Team-3-CSVs
├── figures/                 # Pflichtvisualisierungen
├── tests/                   # pytest-Suite
└── report/report.md
```

## Analysekern

- `hard`: `hard_contact`
- `near`: `hard_contact + dlvo_zone + near_gap`
- `meso`: oben plus `meso_gap`
- Makrozustände: `monomer_gas`, `dimer_dominated`, `trimer_like`,
  `tetra_like`, `loose_four_cluster`, `large_cluster`,
  `mixed_transition`. `tetra_like` ist ein 2D-Kompaktheits-Proxy.
- Persistenzfilter: Runs kürzer als fünf Frames werden ersetzt; raw und
  filtered bleiben immer getrennt erhalten.
- Return Probability: nur Abgänge mit vollständigem Horizont T=50.
- Mean Return Time: T=200; zensierte Endfenster zählen nicht als Nicht-Rückkehr.
- Jitter: reproduzierbare Normalstörungen mit sigma = 1 nm; Label Agreement
  wird auf Rohlabels gemessen.

## Übergabe an Team 3

`data/processed/team3_macrostates.csv` enthält 19,000 Meso-Graph-Sequenzen aus
allen 19 Läufen mit den Spalten `run_id, seed, time, macrostate_raw,
macrostate_filtered, model_type, material_type, A_H, salt_mM, noise,
largest_cluster, mean_degree`. Team 3 sollte bevorzugt `macrostate_filtered`
verwenden; die Rohsequenz bleibt zur Filterdiagnose erhalten.

## Endergebnis kurz

Vier heuristische Attraktor-Kandidaten erfüllen alle fünf Seminarheuristiken:
`cl_retarded`/Fettsäure/Meso/`large_cluster` mit Return Probability 0.40;
`vdw_only`/Fettsäure/Meso/`tetra_like` mit 0.50;
`vdw_only`/Fettsäure/Meso/`large_cluster` mit 0.40; und
`vdw_only`/Fettsäure/Near/`dimer_dominated` mit 0.50. Alle beruhen auf drei
Seeds und sind keine formalen Attraktorbeweise. Details und Grenzen stehen in
`report/report.md`.

## Wichtige Grenzen

- Vorgeclusterte Startbedingungen messen Persistenz, keine spontane
  Clusterbildung aus einer verdünnten Phase.
- `tetra_like` ist kein Beweis für einen 3D-Tetraeder.
- `vdw_only` und `cl_retarded` haben keinen Core-Repulsionsterm; nach Kontakt
  können Protozellen tief überlappen. Details stehen im Bericht.
- Weniger als drei Seeds erlauben keine Seed-Reproduzierbarkeitsaussage.
- Dwell-/Return-Daten sind an finiten Beobachtungsfenstern zensiert.
- Heuristiken im Kandidatenkatalog sind keine formalen Attraktorbeweise.
