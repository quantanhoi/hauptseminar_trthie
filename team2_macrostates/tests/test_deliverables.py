import re
import json
from pathlib import Path

import pandas as pd
import pytest


def _notebook_source(name):
    notebook = json.loads(
        (Path(__file__).parents[1] / 'notebooks' / name).read_text(encoding='utf-8')
    )
    return [''.join(cell.get('source', [])) for cell in notebook['cells']]


def test_report_quantifies_coalescence_artifact():
    text = (Path(__file__).parents[1] / 'report' / 'report.md').read_text(encoding='utf-8')
    for phrase in ['L < −900 nm', '91.8', '85.8', '72.1', '33.8', '0.0']:
        assert phrase in text


def test_report_labels_candidates_as_overlap_qualified_heuristics():
    text = (Path(__file__).parents[1] / 'report' / 'report.md').read_text(encoding='utf-8')
    assert 'Tiefenüberlappung' in text
    assert re.search(r'nicht\s+als\s+Beweis', text, flags=re.IGNORECASE)


def test_notebook03_does_not_claim_single_seed_ensemble():
    sources = _notebook_source('03_robustness_comparison.ipynb')
    joined = '\n'.join(sources)
    assert 'aktuelles Datai-Inventar nicht erfüllt' not in joined
    assert 'aktuell nur einen Seed' not in joined
    assert any('drei Seeds' in source for source in sources)


def test_select_filter_demo_chooses_documented_maximum_filter_effect():
    from src.pipeline import select_filter_demo

    sequences = pd.DataFrame([
        ('hard', 'run_a', 'monomer_gas', 'dimer_dominated'),
        ('hard', 'run_a', 'monomer_gas', 'monomer_gas'),
        ('hard', 'run_a', 'monomer_gas', 'monomer_gas'),
        ('hard', 'run_b', 'monomer_gas', 'dimer_dominated'),
        ('hard', 'run_b', 'dimer_dominated', 'monomer_gas'),
        ('near', 'run_b', 'monomer_gas', 'monomer_gas'),
        ('near', 'run_b', 'monomer_gas', 'dimer_dominated'),
        ('near', 'run_b', 'monomer_gas', 'monomer_gas'),
    ], columns=['graph_type', 'run_id', 'macrostate_raw', 'macrostate_filtered'])

    result = select_filter_demo(sequences)
    assert result['graph_type'] == 'hard'
    assert result['run_id'] == 'run_b'
    assert result['changed'] == 2
