# Team 1 – Physikalisches Basismodell: DLVO, van der Waals und Casimir–Lifshitz

Schrittweise Modellierung der effektiven Wechselwirkungen zwischen präbiotischen
Protozellen (R = 500 nm) im Oberflächenabstandsbereich L = 2–100 nm. Vergleich
von klassischer DLVO-Physik (inkl. nicht-retardierter van-der-Waals-Anziehung)
mit einer retardierten Casimir–Lifshitz-Approximation, plus
Brownian-Paardynamik, 2D-Mehrteilchensimulation undrobuster Mikrodaten für Team 2.

## Setup

```bash
cd team1_forces
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Notebooks ausführen

```bash
.venv/bin/jupyter lab notebooks/
```

oder ohne Oberfläche, mit eingebetteten Ausgaben:

```bash
.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=1800 notebooks/01_force_curves.ipynb
# analog 02_pair_dynamics, 03_cluster_simulation, 04_parameter_sweep
```

Alle Abbildungen landen in `figures/`, die Team-2-Übergabedaten in
`data/processed/`. Notebook 03 löscht die Übergabedateien vor dem Export – ein
Rerun regeneriert sie vollständig (idempotent).

## Projektstruktur

```
team1_forces/
├── src/               # getestete Physik-Bibliothek
│   ├── constants.py       # kB, T_REF, Debye-Längen (§4)
│   ├── potentials.py      # ProtocellForces: vdW, DLVO, CL-retarded (§5–7)
│   ├── force_table.py     # Stützstellen-Tabellen (§9, Schritt 3–4)
│   ├── pair_dynamics.py   # 1D-Paar-Brownian-Dynamik + Zonen (§9, Schritt 7)
│   ├── brownian_cluster.py# vektorisierte 2D-Cluster-Simulation + Gitterstart
│   ├── metrics.py         # Dwell/Escape/Return/Kontakt + Cluster-/Graphmetriken (§11)
│   ├── export.py          # Team-2-CSVs in den exakten §17-Schemata
│   └── plots.py           # gemeinsamer Plot-Stil
├── notebooks/         # 01 Kraftkurven · 02 Paardynamik · 03 Cluster+Export · 04 Sweeps
├── tests/             # pytest-Suite (Physik-Konsistenz, Zonen, Metriken, Export)
├── data/processed/    # positions.csv, pairs.csv, cluster_metrics.csv, parameters.csv
├── figures/           # alle Pflichtplots (§14)
└── report/            # Berichtsentwurf (Deutsch)
```

## Modellmodi — und was niemals addiert wird

| Modus | Inhalt | Physikalischer Status |
|---|---|---|
| `vdw` | U = −A_H·R_eff/(6L), F = −A_H·R_eff/(6L²) | nicht-retardierter Nahbereichs-Grenzfall der Lifshitz-Theorie |
| `dlvo` | elektrostatische Repulsion B·e^(−κL) + vdW + Core C·(L_core/L)^12 | klassische Kolloidphysik |
| `cl_retarded` | F_vdw · r(L), r(L) = 1/(1 + L/L_r)^p | retardierter vdW-Grenzfall |
| Lifshitz-Ausblick | Matsubara-Moden, TE/TM, Schalenmodell | nur Dokumentation (§8), keine Numerik |

**Grundsatz (§3):** `F_total = F_el + F_vdW + F_CL` ist physikalisch problematisch –
vdW ist bereits Teil des Lifshitz-Rahmens. Die Modi werden ausschließlich
 verglichen, nie kombiniert.

## Numerische Stabilität (§18, Fehler 6)

Die Anhangs-Defaults (dt = 1×10⁻⁴ s) erzeugen bei kleinen L numerische
Explosionen (Drift ≫ Box). Alle Dynamik-Läufe verwenden deshalb:

- **dt = 1×10⁻⁷ s** und **Kraftbegrenzung F_max = 20 pN**, sodass der Drift pro
  Schritt ≤ 0.2 nm bleibt (Regel μ·F_max·dt ≤ 0.2 nm, durch Tests abgesichert);
- Konstruktor-Defaults bleiben unverändert wie im Anhang; das tatsächlich
  verwendete dt steht je Run in `parameters.csv`.

**Korrektur gegenüber dem Anhang:** die 2D-Cluster-Schleife des Anhangs
(`forces[i] += F * direction`) kehrt die Vorzeichenkonvention von §5
(F < 0 anziehend) um. Diese Implementierung korrigiert das
(`forces[i] -= F * direction`) – Tests in `tests/test_brownian_cluster.py`
(Äquivalenz zur korrigierten Referenzschleife, Anziehung schließt den Abstand).

## Seed-Politik

Alle Läufe verwenden feste, dokumentierte Seeds. Die Team-2-Übergabe nutzt die
drei Seeds {0, 1, 42} für jeden konfigurierenden N=20-Block; Seed 42 bleibt der
klassische Referenz-Export und 0/1 komplettieren die Ensemble-Statistik.
Run-IDs sind deterministisch aus den Parametern
abgeleitet (`src/export.py:make_run_id`), z. B.
`cl_retarded_A5.0e-21_I100_N50_s42`. Teams können Runs damit exakt vergleichen.

## Übergabeformat an Team 2 (§17)

Der aktuelle Export enthält 19 Runs:

- N = 20: {`vdw`, `dlvo`, `cl_retarded`} × {`A_H = 5e-21` (PMBC),
  `A_H = 0.5e-21` (Fettsäure)} × Seeds {0, 1, 42};
- N = 50: `cl_retarded`/PMBC, Seed 42, nur als getrennte Exploration.

| Datei | Spalten |
|---|---|
| positions.csv | run_id, seed, t, particle_id, x, y, model_type, A_H, lambda_D, noise, T |
| pairs.csv | run_id, seed, t, i, j, L_nm, contact_zone, force_mode |
| cluster_metrics.csv | run_id, seed, t, largest_cluster, mean_degree, n_edges, n_components |
| parameters.csv | run_id, model_type, R_nm, A_H, salt_mM, L_ret_nm, p_ret, dt, mobility, diffusion |

Einheiten: x, y in Metern; L_nm in Nanometern; t in Sekunden; Kräfte in pN,
Energien in U/kBT (§9, Schritt 1). `pairs.csv` enthält nur Paare mit L < 100 nm
(Zone ≠ separated) – entfernte Paare kann Team 2 aus x, y rekonstruieren.
Kontaktdefinition Standard: L < 30 nm (Zonen hard_contact…meso_gap).

## Interpretation (strenge Regel, §10)

Standard-Lifshitz-/CL-Kopplung kann im Bereich **2–30 nm** plausibel zur
Stabilisierung beitragen, besonders für PMBC-artige Protozellen. Für **30–100 nm**
sind Einzelpaar-Kräfte wahrscheinlich schwach; robuste Clusterbildung erfordert
Mehrkörper-, Geometrie- oder Gap-Effekte. **Nicht behauptet wird**, dass CL die
Clusterbildung von 2–100 nm vollständig erklärt.

## Ausblick: Lifshitz-Berechnung (§8, nur Dokumentation)

Die korrekte Zerlegung der Lifshitz-Kraft wäre
F_CL(L) = F₀,long(L,κ) + F₀,TM(L) + F_n≥1^TE/TM(L): Der n=0-longitudinale
Beitrag ist Debye-gescreent (wenige Debye-Längen relevant); die höheren
Matsubara-Moden n ≥ 1 sind für typische Salzlösungen deutlich weniger direkt von
der Ionenbewegung betroffen – deshalb eliminiert Salz die Fluktuationsbeiträge
nicht einfach exponentiell. Für genauere Rechnungen müssen TE- und
TM-Polarisationen getrennt und ein Schalenmodell der Protozelle verwendet
werden. In diesem Projekt bewusst nur numerisch angenähert (r(L)-Faktor).

## Literatur (§20)

- Israelachvili, *Intermolecular and Surface Forces* – DLVO-, vdW- und Hydration-Grundlagen
- Casimir; Lifshitz – Ursprung und Verallgemeinerung fluktuationsinduzierter Kräfte
- Nunes et al. / Spreng et al. – Casimir-Interaktionen zwischen Kugeln in Elektrolyten
- Schoger et al. – universelle Casimir-Interaktionen dielektrischer Kugeln in Salzwasser
- Seyedzahedi, Moradian – Elektrolyten, Schichtmedien, TE/TM, Hamaker-Koeffizienten