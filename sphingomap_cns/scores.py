"""Per-sample module scores and composite indices."""
from __future__ import annotations

import pandas as pd

from .genesets import COMPOSITE_INDICES, MODULES


def zscore_rows(expr: pd.DataFrame, reference: list[str] | None = None) -> pd.DataFrame:
    """Gene-wise z-scores centred and scaled on ``reference`` samples (e.g. controls)."""
    ref = expr if reference is None else expr[reference]
    mu, sd = ref.mean(axis=1), ref.std(axis=1, ddof=1).replace(0, float("nan"))
    return expr.sub(mu, axis=0).div(sd, axis=0)


def module_scores(expr: pd.DataFrame, reference: list[str] | None = None,
                  min_genes: int = 2) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Mean z-score of each module's detected genes per sample, plus composite indices.

    A score of +1 means 'on average one control-SD above the control mean'.
    """
    z = zscore_rows(expr, reference)
    scores, used = {}, {}
    for name, mod in MODULES.items():
        genes = [g for g in mod["genes"] if g in z.index and z.loc[g].notna().any()]
        used[name] = genes
        if len(genes) >= min_genes:
            scores[name] = z.loc[genes].mean(axis=0)
    for name, (up, down) in COMPOSITE_INDICES.items():
        u = [g for g in up if g in z.index and z.loc[g].notna().any()]
        d = [g for g in down if g in z.index and z.loc[g].notna().any()]
        used[name] = u + d
        if len(u) >= 2 and len(d) >= 2:
            scores[name] = z.loc[u].mean(axis=0) - z.loc[d].mean(axis=0)
    return pd.DataFrame(scores), used


def score_label(name: str) -> str:
    if name in MODULES:
        return MODULES[name]["label"]
    return {"rheostat_index": "Rheostat index", "cpa_index": "Ceramide-peroxidation index"}.get(
        name, name.replace("_", " "))
