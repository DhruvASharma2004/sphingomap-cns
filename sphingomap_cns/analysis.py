"""One comparison (one cohort x contrast x stratum, or one user dataset) -> tables, figures, report."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from . import __version__, plots
from .genesets import FOCUS_GENES, MODULES, all_genes, gene_to_module
from .scores import module_scores, score_label
from .stats import correlate, differential_expression, hedges_g, paired_differential_expression

SIG_FDR, SIG_LFC = 0.05, 0.25


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")


def run_comparison(expr: pd.DataFrame, groups: pd.Series, outdir: str | Path, label: str,
                   covariates: pd.DataFrame | None = None, case_label: str = "Case",
                   control_label: str = "Control", pairs: pd.Series | None = None,
                   biomarkers: pd.DataFrame | None = None, meta: dict | None = None) -> dict:
    """Analyse pathway + context genes for Case vs Control samples.

    ``expr`` is log-scale, genes x samples, already restricted to expressed genes.
    ``groups`` holds 'Case' / 'Control' (others ignored). If ``pairs`` is given the
    comparison is within-subject (paired); otherwise a linear model with optional
    covariates is used.
    """
    out = Path(outdir)
    figs = out / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    groups = groups[groups.isin(["Case", "Control"])]
    samples = groups.index.intersection(expr.columns)
    groups = groups.loc[samples]
    n_case, n_ctrl = int((groups == "Case").sum()), int((groups == "Control").sum())
    if n_case < 3 or n_ctrl < 3:
        raise ValueError(f"{label}: need >=3 samples per group (got {n_case} {case_label}, {n_ctrl} {control_label})")

    genes = [g for g in all_genes() if g in expr.index]
    sp = expr.loc[genes, samples]
    paired = pairs is not None
    pd.DataFrame({"group": groups.map({"Case": case_label, "Control": control_label}),
                  **({"pair": pairs.reindex(samples)} if paired else {})}).to_csv(out / "sample_groups.csv")

    # --- gene level -----------------------------------------------------------
    if paired:
        de = paired_differential_expression(sp, groups, pairs.reindex(samples), "Case", "Control")
    else:
        cov = covariates.reindex(samples) if covariates is not None else None
        de = differential_expression(sp, groups, cov)
    mod = gene_to_module()
    de.insert(0, "module", de.index.map(lambda g: MODULES[mod[g]]["label"]))
    de.insert(1, "kind", de.index.map(lambda g: MODULES[mod[g]]["kind"]))
    de.to_csv(out / "differential_expression.csv")

    # --- scores ---------------------------------------------------------------
    ref = list(groups[groups == "Control"].index)
    scores, used = module_scores(sp, reference=ref)
    scores.insert(0, "group", groups.map({"Case": case_label, "Control": control_label}))
    scores.to_csv(out / "sample_scores.csv")
    num = scores.drop(columns="group")
    if paired:
        st = paired_differential_expression(num.T, groups, pairs.reindex(samples), "Case", "Control")
        st = st.rename(columns={"log2FC": "mean_difference", "cohens_dz": "effect"})
    else:
        st = differential_expression(num.T, groups, covariates.reindex(samples) if covariates is not None else None)
        st = st.rename(columns={"log2FC": "mean_difference"})
        st["effect"] = st["hedges_g"]
    st.index.name = "score"
    st.to_csv(out / "score_tests.csv")

    # --- biomarker correlations ---------------------------------------------------
    corr = pd.DataFrame()
    if biomarkers is not None and not biomarkers.empty:
        corr = correlate(num, biomarkers.reindex(num.index))
        corr.to_csv(out / "biomarker_correlations.csv", index=False)

    # --- figures --------------------------------------------------------------
    cmp = f"{case_label} vs {control_label}"
    plots.volcano(de, figs / "volcano.png", title=f"{label}: {cmp}", lfc=SIG_LFC,
                  xlabel=f"log2 fold change ({cmp})")
    plots.pathway_map(de, figs / "pathway_map.png", title=f"{label}: sphingolipid-peroxidation pathway, {cmp}")
    plots.gene_heatmap(sp, groups, figs / "heatmap.png", title=f"{label}: pathway and context genes",
                       case_label=case_label, control_label=control_label)
    plots.score_boxplot(num, groups, figs / "module_scores.png", title=f"{label}: module scores",
                        labels={"Case": case_label, "Control": control_label})
    case_scores = num.loc[groups[groups == "Case"].index]
    if len(case_scores) >= 8:
        plots.correlation_heatmap(case_scores, figs / "score_correlation.png",
                                  title=f"{label}: score co-variation within {case_label}")
    if paired:
        keys = [c for c in ["cpa_index", "sphingomyelin_cycle", "treg_axis", "microglia_myeloid"] if c in num]
        plots.paired_plot(num, groups, pairs.reindex(samples), keys, figs / "paired_scores.png",
                          case_label, control_label, title=f"{label}: within-subject change")
    if not corr.empty:
        plots.biomarker_heatmap(corr, figs / "biomarker_correlation.png",
                                title=f"{label}: scores vs measured biomarkers (Spearman)")

    sig = de[(de.fdr < SIG_FDR) & (de.log2FC.abs() >= SIG_LFC)]
    summary = {
        "label": label, "version": __version__, "date": str(date.today()),
        "comparison": cmp, "design": "paired" if paired else "unpaired",
        "covariates": de.attrs.get("covariates", []), "n_case": n_case, "n_control": n_ctrl,
        "n_pairs": int(de.attrs.get("n_pairs", 0)) if paired else None,
        "n_genes_tested": int(de["p"].notna().sum()),
        "missing_genes": [g for g in all_genes() if g not in expr.index],
        "n_significant": len(sig),
        "up": sig[sig.log2FC > 0].sort_values("log2FC", ascending=False).index.tolist(),
        "down": sig[sig.log2FC < 0].sort_values("log2FC").index.tolist(),
        "focus_genes": de.reindex([g for g in FOCUS_GENES if g in de.index])[["log2FC", "fdr"]]
        .reset_index().to_dict(orient="records"),
        "scores": st[["mean_difference", "effect", "p", "fdr"]].reset_index().to_dict(orient="records"),
        "score_genes": used, **(meta or {}),
    }
    if not corr.empty:
        summary["biomarker_correlations"] = corr.round(6).to_dict(orient="records")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=_json))
    write_report(summary, de, out, corr)
    return {"summary": summary, "de": de, "scores": num, "score_tests": st, "groups": groups}


def _json(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return None if np.isnan(x) else float(x)
    return str(x)


def score_effects(scores: pd.DataFrame, groups: pd.Series) -> pd.DataFrame:
    """Hedges' g for each score (used by the atlas)."""
    rows = {}
    for c in scores.columns:
        a = scores.loc[groups[groups == "Case"].index, c].dropna().values
        b = scores.loc[groups[groups == "Control"].index, c].dropna().values
        rows[c] = hedges_g(a, b)
    return pd.DataFrame(rows, index=["g", "var"]).T


def write_report(s: dict, de: pd.DataFrame, out: Path, corr: pd.DataFrame | None = None) -> None:
    eff = "Cohen's dz" if s["design"] == "paired" else "Hedges' g"
    n_line = (f"- {s['n_pairs']} subjects with both timepoints (paired analysis)" if s["design"] == "paired"
              else f"- {s['comparison'].split(' vs ')[0]}: **{s['n_case']}**, "
                   f"{s['comparison'].split(' vs ')[1]}: **{s['n_control']}**")
    L = [f"# sphingomap-CNS report: {s['label']}", "",
         f"_sphingomap-CNS v{s['version']}, generated {s['date']}_", ""]
    if s.get("source"):
        L += [f"Source: {s['source']}", ""]
    L += ["## Design", "", n_line,
          f"- Model: {'paired t-test + Wilcoxon' if s['design'] == 'paired' else 'linear model'}"
          + (f", adjusted for {', '.join(s['covariates'])}" if s["covariates"] else ""),
          f"- Genes tested: {s['n_genes_tested']}"
          + (f" (not in data / not expressed: {', '.join(s['missing_genes'])})" if s["missing_genes"] else ""),
          "", "## Gene-level changes", "",
          f"{s['n_significant']} genes with FDR < {SIG_FDR} and |log2FC| >= {SIG_LFC}.", "",
          f"- Up: {', '.join(s['up']) or '-'}", f"- Down: {', '.join(s['down']) or '-'}", "",
          "![pathway](figures/pathway_map.png)", "", "![volcano](figures/volcano.png)", "",
          "### Proposal focus genes", "", "| Gene | log2FC | FDR |", "|---|---:|---:|"]
    for r in s["focus_genes"]:
        if r["log2FC"] is not None and not pd.isna(r["log2FC"]):
            L.append(f"| {r['gene']} | {r['log2FC']:+.2f} | {r['fdr']:.2e} |")
    L += ["", "### Top 25 genes", "", "| Gene | Module | log2FC | FDR |", "|---|---|---:|---:|"]
    for g, r in de.dropna(subset=["fdr"]).head(25).iterrows():
        L.append(f"| {g} | {r.module} | {r.log2FC:+.2f} | {r.fdr:.2e} |")
    L += ["", "## Module scores and indices", "",
          "Scores are mean z-scores relative to the control group. The rheostat index is "
          "pro-survival (S1P/GSL) minus pro-ceramide genes; the ceramide-peroxidation (CPA) index is "
          "ceramide-generation + peroxidation-driver genes minus ceramide-clearance + antioxidant genes.", "",
          f"| Score | Mean difference | {eff} | FDR |", "|---|---:|---:|---:|"]
    for t in s["scores"]:
        if t["p"] is None or pd.isna(t["p"]):
            continue
        L.append(f"| {score_label(t['score'])} | {t['mean_difference']:+.2f} | {t['effect']:+.2f} | {t['fdr']:.2e} |")
    L += ["", "![scores](figures/module_scores.png)", ""]
    if (out / "figures" / "paired_scores.png").exists():
        L += ["![paired](figures/paired_scores.png)", ""]
    if (out / "figures" / "score_correlation.png").exists():
        L += ["![correlation](figures/score_correlation.png)", ""]
    if corr is not None and not corr.empty:
        L += ["## Correlation with measured biomarkers", "", "| Score | Biomarker | n | rho | FDR |",
              "|---|---|---:|---:|---:|"]
        for _, r in corr.head(20).iterrows():
            L.append(f"| {score_label(r.score)} | {r.target} | {r.n} | {r.spearman_rho:+.2f} | {r.fdr:.2e} |")
        L += ["", "![biomarkers](figures/biomarker_correlation.png)", ""]
    L += ["![heatmap](figures/heatmap.png)", "", "## Caveats", "",
          "- mRNA / protein abundance is not enzyme activity or lipid concentration; confirm with "
          "lipidomics (LC-MS/MS, HPTLC).",
          "- Module scores and indices are exploratory transcript-level heuristics, not validated biomarkers.",
          "- Post-mortem bulk tissue mixes cell types; changes can reflect cell-composition shifts "
          "(e.g. neuron loss, gliosis) rather than per-cell regulation."]
    if s["design"] == "paired" and corr is not None and not corr.empty:
        L.append("- Biomarker correlations pool both timepoints, so each subject contributes two points; "
                 "treat them as descriptive, not as independent-sample tests.")
    L.append("")
    (out / "REPORT.md").write_text("\n".join(L))
