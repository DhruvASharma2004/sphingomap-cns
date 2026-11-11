"""Multi-cohort Sphingolipid Pathway Atlas: per-stratum analyses + cross-cohort synthesis."""
from __future__ import annotations

import json
import traceback
from pathlib import Path

import pandas as pd

from . import __version__, geo, plots
from .analysis import run_comparison, score_effects, slug
from .design import (
    assign_groups,
    assign_strata,
    ensure_log2,
    expressed_genes,
    log_cpm,
    parse_covariates,
    usable_covariates,
)
from .genesets import FOCUS_GENES, MODULES, all_genes, gene_to_module
from .registry import COHORTS
from .report import write_atlas_html
from .scores import score_label
from .stats import random_effects_meta


def prepare_cohort(cid: str, datadir: str | Path, cfg: dict | None = None) -> dict:
    """Download (if needed) and load one GEO cohort as log-scale genes x samples + annotation."""
    cfg = cfg or COHORTS[cid]
    files = geo.fetch_series(cid, datadir, cfg["platform"], cfg.get("gpl"))
    ann, table = geo.load_series(files["series_matrix"])
    if cfg["platform"] == "rnaseq":
        counts = geo.load_ncbi_counts(files["counts"], files["gene_annot"])
        counts = counts.loc[:, counts.columns.intersection(ann.index)]
        expr, transformed = log_cpm(counts), "log2 CPM (NCBI raw counts)"
    else:
        expr = geo.probes_to_genes(table, geo.parse_platform(files["platform"]))
        expr, logged = ensure_log2(expr)
        transformed = "log2(series-matrix values)" if logged else "series-matrix values (already log scale)"
    return {"expr": expr, "ann": ann.loc[ann.index.intersection(expr.columns)], "platform": cfg["platform"],
            "scale": transformed}


def analyse_cohort(cid: str, data: dict, cfg: dict, outdir: Path) -> list[dict]:
    """Run every contrast x stratum for one cohort; returns one record per comparison."""
    expr, ann = data["expr"], data["ann"]
    covs = parse_covariates(ann)
    strata = assign_strata(ann, cfg.get("strata"))
    records = []
    for contrast, (case_pat, ctrl_pat) in cfg["contrasts"].items():
        groups_all = assign_groups(ann, case_pat, ctrl_pat, cfg.get("exclude"))
        for stratum in [s for s in (cfg.get("strata") or {"All": None})]:
            idx = strata[strata == stratum].index
            g = groups_all.loc[idx].dropna()
            label = f"{cid} {contrast}" + ("" if stratum == "All" else f" - {stratum}")
            sub = outdir / cid / slug(f"{contrast}_{stratum}")
            if (g == "Case").sum() < 3 or (g == "Control").sum() < 3:
                records.append({"cohort": cid, "contrast": contrast, "stratum": stratum, "status": "skipped",
                                "reason": f"{(g == 'Case').sum()} case / {(g == 'Control').sum()} control samples"})
                continue
            e = expr.loc[:, g.index]
            keep = expressed_genes(e, data["platform"])
            e = e.loc[e.index.intersection(keep)]
            cov = usable_covariates(covs, g.index)
            res = run_comparison(e, g, sub, label, covariates=cov, case_label=contrast,
                                 meta={"cohort": cid, "contrast": contrast, "stratum": stratum,
                                       "compartment": cfg.get("compartment", ""), "scale": data["scale"],
                                       "source": f"{cfg.get('title', cid)} ({cfg.get('reference', '')})"})
            se = score_effects(res["scores"], res["groups"])
            records.append({"cohort": cid, "contrast": contrast, "stratum": stratum, "status": "ok",
                            "compartment": cfg.get("compartment", ""), "dir": str(sub.relative_to(outdir)),
                            "n_case": res["summary"]["n_case"], "n_control": res["summary"]["n_control"],
                            "covariates": res["summary"]["covariates"], "de": res["de"],
                            "score_tests": res["score_tests"], "score_g": se})
    return records


def synthesize(records: list[dict], outdir: Path, title: str = "sphingomap-CNS atlas") -> dict:
    """Cross-cohort tables, figures and reports from per-stratum results."""
    ok = [r for r in records if r["status"] == "ok"]
    figs = outdir / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    if not ok:
        raise RuntimeError("No comparison had enough samples; see atlas_runs.csv")
    col = {id(r): f"{r['contrast']} | {r['cohort']} | {r['stratum']}".replace(" | All", "") for r in ok}
    order = sorted(ok, key=lambda r: (r["contrast"], r.get("compartment", ""), r["cohort"], r["stratum"]))
    cols = [col[id(r)] for r in order]
    genes = [g for g in all_genes() if any(g in r["de"].index for r in ok)]

    def gene_tab(field):
        return pd.DataFrame({col[id(r)]: r["de"][field].reindex(genes) for r in order})[cols]

    G, V, Q, LFC = gene_tab("hedges_g"), gene_tab("g_var"), gene_tab("fdr"), gene_tab("log2FC")
    long = pd.concat([r["de"].assign(cohort=r["cohort"], contrast=r["contrast"], stratum=r["stratum"],
                                     compartment=r.get("compartment", "")) for r in order])
    long.index.name = "gene"
    long.to_csv(outdir / "atlas_gene_effects_long.csv")
    G.to_csv(outdir / "atlas_hedges_g.csv")
    Q.to_csv(outdir / "atlas_fdr.csv")

    scores = list(dict.fromkeys(s for r in ok for s in r["score_g"].index))
    SG = pd.DataFrame({col[id(r)]: r["score_g"]["g"].reindex(scores) for r in order})[cols]
    SQ = pd.DataFrame({col[id(r)]: r["score_tests"]["fdr"].reindex(scores) for r in order})[cols]
    SG.to_csv(outdir / "atlas_score_hedges_g.csv")

    # Meta-analysis per contrast (disease) across strata.
    metas = {}
    for contrast in dict.fromkeys(r["contrast"] for r in order):
        cs = [col[id(r)] for r in order if r["contrast"] == contrast]
        if len(cs) < 2:
            continue
        m = random_effects_meta(G[cs], V[cs])
        m.insert(0, "contrast", contrast)
        m["n_strata_up"] = ((G[cs] > 0) & (Q[cs] < 0.05)).sum(axis=1)
        m["n_strata_down"] = ((G[cs] < 0) & (Q[cs] < 0.05)).sum(axis=1)
        metas[contrast] = m
    meta = pd.concat(metas.values()) if metas else pd.DataFrame()
    if not meta.empty:
        meta.index.name = "gene"
        meta.to_csv(outdir / "atlas_meta_analysis.csv")

    plots.atlas_gene_heatmap(G, Q, figs / "atlas_genes.png",
                             title="Sphingolipid and neuroinflammatory genes across cohorts (Hedges' g)")
    plots.atlas_score_heatmap(SG, SQ, figs / "atlas_scores.png", title="Module scores across cohorts (Hedges' g)")
    for contrast, m in metas.items():
        plots.pathway_map(m.rename(columns={"g_meta": "value"}), figs / f"pathway_meta_{slug(contrast)}.png",
                          value="value", title=f"{contrast} vs control: random-effects meta-analysis across strata",
                          cbar_label="meta Hedges' g (black outline: FDR < 0.05)")

    runs = pd.DataFrame([{k: v for k, v in r.items() if k not in ("de", "score_tests", "score_g")}
                         for r in records])
    runs.to_csv(outdir / "atlas_runs.csv", index=False)
    summary = {"version": __version__, "title": title, "comparisons": runs.to_dict(orient="records"),
               "meta_top": {c: m.dropna(subset=["fdr"]).sort_values("p").head(15).round(5).reset_index()
                            .to_dict(orient="records") for c, m in metas.items()}}
    (outdir / "atlas_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    write_atlas_markdown(outdir, runs, metas, SG, SQ)
    write_atlas_html(outdir, title, runs, G, Q, LFC, SG, SQ, meta)
    return summary


def build_atlas(cohort_ids: list[str], datadir: str | Path, outdir: str | Path,
                prepared: dict[str, dict] | None = None, registry: dict | None = None) -> dict:
    """Fetch, analyse and synthesise. ``prepared``/``registry`` let tests and the demo skip GEO."""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    registry = registry or COHORTS
    records = []
    for cid in cohort_ids:
        cfg = registry[cid]
        try:
            data = prepared[cid] if prepared and cid in prepared else prepare_cohort(cid, datadir, cfg)
            print(f"[{cid}] {data['expr'].shape[1]} samples, {data['expr'].shape[0]} genes ({data['scale']})")
            records += analyse_cohort(cid, data, cfg, out)
        except Exception as exc:  # keep going; one broken cohort should not sink the atlas
            print(f"[{cid}] FAILED: {exc}")
            (out / cid).mkdir(parents=True, exist_ok=True)
            (out / cid / "ERROR.txt").write_text(traceback.format_exc())
            records.append({"cohort": cid, "contrast": "", "stratum": "", "status": "failed", "reason": str(exc)})
    for r in records:
        if r["status"] != "ok":
            print(f"  - {r['cohort']} {r['contrast']} {r['stratum']}: {r['status']} ({r.get('reason', '')})")
    return synthesize(records, out)


def write_atlas_markdown(out: Path, runs: pd.DataFrame, metas: dict, SG: pd.DataFrame, SQ: pd.DataFrame):
    L = ["# sphingomap-CNS: Sphingolipid Pathway Atlas", "",
         f"_sphingomap-CNS v{__version__}_", "",
         "Open `atlas.html` for the interactive version (sortable gene table, per-stratum reports).", "",
         "## Comparisons", "", "| Contrast | Cohort | Stratum | Case | Control | Covariates | Status |",
         "|---|---|---|---:|---:|---|---|"]
    for _, r in runs.iterrows():
        cov = ", ".join(r["covariates"]) if isinstance(r.get("covariates"), list) else ""
        st = r["status"] if r["status"] == "ok" else f"{r['status']}: {r.get('reason', '')}"
        n1 = "" if pd.isna(r.get("n_case")) else int(r["n_case"])
        n2 = "" if pd.isna(r.get("n_control")) else int(r["n_control"])
        link = f"[{r['stratum']}]({r['dir']}/REPORT.md)" if r["status"] == "ok" else r["stratum"]
        L.append(f"| {r['contrast']} | {r['cohort']} | {link} | {n1} | {n2} | {cov} | {st} |")
    L += ["", "## Atlas", "", "![genes](figures/atlas_genes.png)", "", "![scores](figures/atlas_scores.png)", ""]
    for contrast, m in metas.items():
        top = m.dropna(subset=["fdr"]).sort_values("p")
        foc = m.reindex([g for g in FOCUS_GENES if g in m.index])
        L += [f"## {contrast} vs control: random-effects meta-analysis", "",
              f"![meta](figures/pathway_meta_{slug(contrast)}.png)", "",
              "| Gene | Module | meta g | 95% CI | I² | strata up / down (FDR<0.05) | FDR |",
              "|---|---|---:|---|---:|---|---:|"]
        mod = gene_to_module()
        for g, r in pd.concat([top.head(15), foc[~foc.index.isin(top.head(15).index)]]).iterrows():
            if pd.isna(r.g_meta):
                continue
            L.append(f"| {g} | {MODULES[mod[g]]['label']} | {r.g_meta:+.2f} | {r.ci_low:+.2f} to {r.ci_high:+.2f} "
                     f"| {r.I2:.0%} | {int(r.n_strata_up)} / {int(r.n_strata_down)} of {int(r.k)} | {r.fdr:.2e} |")
        L.append("")
    L += ["## Module scores (Hedges' g, case vs control)", "",
          "| Score | " + " | ".join(SG.columns) + " |", "|---|" + "---:|" * len(SG.columns)]
    for s in SG.index:
        cells = [("" if pd.isna(v) else f"{v:+.2f}{'*' if pd.notna(q) and q < 0.05 else ''}")
                 for v, q in zip(SG.loc[s], SQ.loc[s], strict=True)]
        L.append(f"| {score_label(s)} | " + " | ".join(cells) + " |")
    L += ["", "\\* FDR < 0.05 within that stratum.", "", "## How to read this", "",
          "- **Hedges' g** is the standardised case-control difference (0.2 small, 0.5 medium, 0.8 large).",
          "- **Meta-analysis** pools strata of the same disease with DerSimonian-Laird random effects. Brain "
          "regions from the same donors are not independent, so pooled p-values are optimistic; read the "
          "'strata up/down' column and I² (between-stratum heterogeneity) alongside them.",
          "- Bulk post-mortem tissue: neuron loss and gliosis shift cell composition, so a change can reflect "
          "which cells are present rather than per-cell regulation. Blood cohorts reflect circulating "
          "leukocytes, the compartment COYA 302 acts on directly.",
          "- Transcript changes are hypotheses for lipid measurement (Phase 2), not lipid measurements.", ""]
    (out / "ATLAS_REPORT.md").write_text("\n".join(L))
