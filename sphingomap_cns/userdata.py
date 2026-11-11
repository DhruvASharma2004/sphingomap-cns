"""Run sphingomap-CNS on your own (e.g. sponsor) data: bulk, proteomics or pseudobulked single-cell.

Inputs
------
expression   features x samples table (CSV/TSV, optionally .gz). First column = gene symbol
             (protein assays: the gene symbol of the target protein). Values can be raw counts
             (``--counts``), linear intensities (auto log2) or already log-scale.
sample sheet one row per sample. Required: ``sample`` and a group column. Optional: subject ID
             for paired/longitudinal designs, stratum (tissue / cell type), covariates (age, sex)
             and any numeric biomarker columns (4-HNE, MDA, NfL, ALSFRS-R...).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .analysis import run_comparison, slug
from .design import ensure_log2, expressed_genes, log_cpm
from .geo import harmonize_symbols


def read_table(path: str | Path, index_col=0) -> pd.DataFrame:
    path = Path(path)
    name = path.name.lower().removesuffix(".gz")
    sep = "," if name.endswith(".csv") else "\t"
    return pd.read_csv(path, sep=sep, index_col=index_col)


def load_user_expression(path, counts: bool = False) -> tuple[pd.DataFrame, str]:
    expr = read_table(path).apply(pd.to_numeric, errors="coerce")
    expr = expr[expr.index.notna()]
    if counts:
        expr = harmonize_symbols(expr.groupby(level=0).sum())
        return log_cpm(expr), "rnaseq"
    expr = harmonize_symbols(expr)
    expr, _ = ensure_log2(expr)
    return expr, "array"


def run_user(expression, samples, outdir, case: str, control: str, group_col: str = "group",
             pair_col: str | None = None, stratum_col: str | None = None, subset: list[str] | None = None,
             biomarkers: list[str] | None = None, covariates: list[str] | None = None,
             counts: bool = False, label: str = "dataset") -> list[dict]:
    expr, platform = load_user_expression(expression, counts)
    sheet = read_table(samples, index_col=None)
    if "sample" not in sheet.columns:
        raise ValueError("Sample sheet needs a 'sample' column")
    sheet["sample"] = sheet["sample"].astype(str)
    sheet = sheet.set_index("sample")
    for cond in subset or []:
        col, val = cond.split("=", 1)
        sheet = sheet[sheet[col].astype(str) == val]
    missing = sheet.index.difference(expr.columns)
    if len(missing):
        print(f"warning: {len(missing)} samples in the sheet are not in the expression table: {list(missing)[:5]}")
    sheet = sheet.loc[sheet.index.intersection(expr.columns)]
    for col in [group_col, pair_col, stratum_col, *(biomarkers or []), *(covariates or [])]:
        if col and col not in sheet.columns:
            raise ValueError(f"Column '{col}' not in sample sheet (have: {list(sheet.columns)})")

    groups_all = sheet[group_col].astype(str).map({case: "Case", control: "Control"})
    strata = sheet[stratum_col].astype(str) if stratum_col else pd.Series("All", index=sheet.index)
    bm = sheet[biomarkers].apply(pd.to_numeric, errors="coerce") if biomarkers else None
    cov = None
    if covariates:
        cov = pd.DataFrame(index=sheet.index)
        for c in covariates:
            v = pd.to_numeric(sheet[c], errors="coerce")
            if v.notna().mean() < 0.5:  # categorical -> 0/1 for the first level
                lv = sheet[c].astype(str)
                v = (lv == sorted(lv.unique())[0]).astype(float)
            cov[c] = v.fillna(v.mean())
    results = []
    for st in sorted(strata.unique()):
        idx = strata[strata == st].index
        g = groups_all.loc[idx].dropna()
        e = expr.loc[:, g.index]
        e = e.loc[e.index.intersection(expressed_genes(e, platform))] if platform == "rnaseq" else e
        e = e.loc[e.notna().mean(axis=1) >= 0.5]
        lab = label if st == "All" else f"{label} - {st}"
        sub = Path(outdir) if st == "All" else Path(outdir) / slug(st)
        try:
            res = run_comparison(e, g, sub, lab, covariates=cov, case_label=case, control_label=control,
                                 pairs=sheet.loc[g.index, pair_col].astype(str) if pair_col else None,
                                 biomarkers=bm.loc[g.index] if bm is not None else None)
            results.append(res["summary"])
            print(f"[{lab}] {res['summary']['n_significant']} significant genes -> {sub}/REPORT.md")
        except ValueError as exc:
            print(f"[{lab}] skipped: {exc}")
    return results


def pseudobulk(cells: str | Path, out: str | Path, sample_col: str = "sample", celltype_col: str | None = None,
               min_cells: int = 20, stat: str = "mean", metadata: str | Path | None = None) -> Path:
    """Aggregate a cells x markers table (CyTOF / flow / single-cell proteomics) to pseudobulk.

    Writes ``<out>_expression.tsv`` (markers x pseudo-samples) and ``<out>_samples.csv``
    (pseudo-sample, source_sample, cell_type, n_cells) so the result can go straight into ``run``.
    ``metadata`` (CSV with a ``sample`` column: group, subject, timepoint, biomarkers...) is joined
    onto each pseudo-sample via its source sample. Marker columns must be gene symbols.
    """
    df = read_table(cells, index_col=None)
    keys = [sample_col] + ([celltype_col] if celltype_col else [])
    markers = [c for c in df.columns if c not in keys and pd.api.types.is_numeric_dtype(df[c])]
    grp = df.groupby(keys)
    agg = grp[markers].median() if stat == "median" else grp[markers].mean()
    n = grp.size().rename("n_cells")
    agg, n = agg[n >= min_cells], n[n >= min_cells]
    names = ["__".join(map(str, k)) if isinstance(k, tuple) else str(k) for k in agg.index]
    expr = agg.copy()
    expr.index = names
    expr = expr.T
    expr.index.name = "gene"
    sheet = pd.DataFrame({"sample": names, "source_sample": [k[0] if isinstance(k, tuple) else k for k in agg.index],
                          "n_cells": n.values})
    if celltype_col:
        sheet["cell_type"] = [k[1] for k in agg.index]
    if metadata:
        md = read_table(metadata, index_col=None)
        md["sample"] = md["sample"].astype(str)
        sheet["source_sample"] = sheet["source_sample"].astype(str)
        sheet = sheet.merge(md.rename(columns={"sample": "source_sample"}), on="source_sample", how="left")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    expr.to_csv(f"{out}_expression.tsv", sep="\t")
    sheet.to_csv(f"{out}_samples.csv", index=False)
    print(f"{len(names)} pseudo-samples x {len(markers)} markers -> {out}_expression.tsv, {out}_samples.csv")
    return Path(f"{out}_expression.tsv")
