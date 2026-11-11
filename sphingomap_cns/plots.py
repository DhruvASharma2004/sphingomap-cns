"""Publication-style figures (matplotlib, PNG)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

from .genesets import CONTEXT, MODULES, PATHWAY_LAYOUT, PATHWAY_NODES, SPHINGOLIPID, gene_to_module
from .scores import score_label

KIND_COLORS = {SPHINGOLIPID: "#2a78d6", CONTEXT: "#eb6834"}
KIND_LABELS = {SPHINGOLIPID: "Sphingolipid pathway", CONTEXT: "Neuroinflammatory context"}
GROUP_COLORS = {"Control": "#8fb3dd", "Case": "#e0795a"}
DIVERGING = "RdBu_r"
INK, MUTED = "#222222", "#8a8984"

plt.rcParams.update({"font.size": 9.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK,
                     "ytick.color": INK, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.dpi": 160, "font.family": "DejaVu Sans"})


def _ordered_genes(index) -> list[str]:
    return [g for name in MODULES for g in MODULES[name]["genes"] if g in index]


def _module_spans(genes: list[str]):
    """(module label, first row, last row) for consecutive runs of the same module."""
    mod = gene_to_module()
    spans, start = [], 0
    for i in range(1, len(genes) + 1):
        if i == len(genes) or mod[genes[i]] != mod[genes[start]]:
            spans.append((MODULES[mod[genes[start]]]["label"], start, i - 1))
            start = i
    return spans


def _label_modules(ax, genes, x=-0.02, transform=None):
    for label, a, b in _module_spans(genes):
        ax.annotate("", xy=(x, a - 0.4), xytext=(x, b + 0.4), xycoords=("axes fraction", "data"),
                    arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 1.2})
        ax.text(x - 0.012, (a + b) / 2, label, transform=ax.get_yaxis_transform(), ha="right",
                va="center", fontsize=7.5, color=INK)


def volcano(de: pd.DataFrame, path, fdr: float = 0.05, lfc: float = 0.25, title: str = "",
            xlabel: str = "log2 fold change (case vs control)"):
    mod = gene_to_module()
    d = de.dropna(subset=["log2FC", "fdr"]).copy()
    d["nlp"] = -np.log10(d["fdr"].clip(lower=1e-300))
    d["kind"] = d.index.map(lambda g: MODULES[mod[g]]["kind"] if g in mod else CONTEXT)
    sig = (d.fdr < fdr) & (d.log2FC.abs() >= lfc)
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.scatter(d.log2FC[~sig], d.nlp[~sig], s=22, color="#c9c8c2", edgecolor="none", label="Not significant")
    for kind, color in KIND_COLORS.items():
        s = d[sig & (d.kind == kind)]
        ax.scatter(s.log2FC, s.nlp, s=40, color=color, edgecolor="white", lw=0.8, label=KIND_LABELS[kind])
    lab = d[sig].nlargest(18, "nlp")
    xr = max(d.log2FC.abs().max(), lfc) * 2 or 1
    yr = max(d.nlp.max(), 1)
    placed: list[tuple[float, float]] = []
    for g, r in lab.sort_values("nlp").iterrows():
        tx, ty = r.log2FC + 0.015 * xr, r.nlp
        while any(abs(tx - px) < 0.13 * xr and abs(ty - py) < 0.05 * yr for px, py in placed):
            ty += 0.05 * yr
        placed.append((tx, ty))
        ax.annotate(g, (r.log2FC, r.nlp), xytext=(tx, ty), textcoords="data", fontsize=7.5, color=INK,
                    va="center", arrowprops={"arrowstyle": "-", "color": "#bdbcb6", "lw": 0.5}
                    if abs(ty - r.nlp) > 0.02 * yr else None)
    ax.set_ylim(top=max(yr, max((p[1] for p in placed), default=0)) * 1.06)
    ax.axhline(-np.log10(fdr), ls="--", c=MUTED, lw=0.7)
    for x in (-lfc, lfc):
        ax.axvline(x, ls="--", c=MUTED, lw=0.7)
    ax.set(xlabel=xlabel, ylabel="-log10 FDR", title=title)
    ax.legend(fontsize=7.5, frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1))
    fig.savefig(path)
    plt.close(fig)


def gene_heatmap(expr: pd.DataFrame, groups: pd.Series, path, title: str = "",
                 case_label: str = "Case", control_label: str = "Control"):
    """Row-z-scored heatmap of pathway genes, samples ordered Control | Case."""
    genes = _ordered_genes(expr.index)
    order = list(groups[groups == "Control"].index) + list(groups[groups == "Case"].index)
    z = expr.loc[genes, order]
    z = z.sub(z.mean(axis=1), axis=0).div(z.std(axis=1).replace(0, 1), axis=0).clip(-3, 3)
    fig, ax = plt.subplots(figsize=(8.5, 0.16 * len(genes) + 1.6))
    im = ax.imshow(z.values, aspect="auto", cmap=DIVERGING, vmin=-3, vmax=3, interpolation="nearest")
    n_c = (groups.loc[order] == "Control").sum()
    ax.axvline(n_c - 0.5, c="k", lw=1)
    ax.set_yticks(range(len(genes)), genes, fontsize=6.5)
    ax.yaxis.tick_right()
    ax.set_xticks([n_c / 2, n_c + (len(order) - n_c) / 2],
                  [f"{control_label} (n={n_c})", f"{case_label} (n={len(order) - n_c})"])
    for spine in ax.spines.values():
        spine.set_visible(False)
    _label_modules(ax, genes)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.08, label="row z-score")
    fig.savefig(path)
    plt.close(fig)


def pathway_map(de: pd.DataFrame, path, title: str = "", value: str = "log2FC",
                cbar_label: str = "log2FC (black outline: FDR < 0.05)", fdr_col: str = "fdr"):
    """Schematic pathway with enzymes coloured by effect; inflammatory input and peroxidation output."""
    fig, ax = plt.subplots(figsize=(10.5, 7.6))
    vals = de[value].reindex(list(PATHWAY_LAYOUT)).abs()
    vmax = max(0.5, float(vals.max(skipna=True)) if vals.notna().any() else 0.5)
    norm = TwoSlopeNorm(vcenter=0, vmin=-vmax, vmax=vmax)
    cmap = plt.get_cmap(DIVERGING)
    for label, (x, y) in PATHWAY_NODES.items():
        ax.text(x, y, label, ha="center", va="center", fontsize=9.5, weight="bold", color=INK,
                bbox={"boxstyle": "round,pad=0.4", "fc": "#f3f3f1", "ec": MUTED})
    arrows = [((0.5, 6.9), (4.3, 4.8)),    # de novo -> ceramide
              ((4.1, 4.3), (1.4, 3.9)),    # ceramide -> SM
              ((1.2, 3.5), (4.1, 4.2)),    # SM -> ceramide (SMase)
              ((4.9, 4.4), (5.6, 4.05)),   # ceramide -> sphingosine
              ((6.8, 4.0), (7.9, 4.0)),    # sphingosine -> S1P
              ((4.7, 4.9), (6.2, 8.1)),    # ceramide -> GSL
              ((0.9, 0.85), (2.6, 2.4)),   # cytokines -> SMases
              ((4.8, 4.15), (6.6, 0.55))]  # ceramide -> ROS / peroxidation
    for (x0, y0), (x1, y1) in arrows:
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops={"arrowstyle": "->", "color": "#a7a6a0", "lw": 1.4,
                                "connectionstyle": "arc3,rad=0.15"})
    for gene, (x, y) in PATHWAY_LAYOUT.items():
        if gene in de.index and pd.notna(de.loc[gene, value]):
            v, q = de.loc[gene, value], de.loc[gene, fdr_col] if fdr_col in de.columns else np.nan
            sig = pd.notna(q) and q < 0.05
            fc, ec, lw = cmap(norm(v)), ("k" if sig else "#bdbcb6"), (1.6 if sig else 0.6)
            tc = "white" if abs(norm(v) - 0.5) > 0.33 else "black"
        else:
            fc, ec, lw, tc = "white", "#e2e1dc", 0.6, "#a7a6a0"
        ax.text(x, y - 0.35 if y > 7.2 else y, gene, ha="center", va="center", fontsize=8, color=tc,
                bbox={"boxstyle": "round,pad=0.25", "fc": fc, "ec": ec, "lw": lw})
    ax.text(3.35, 0.6, "drivers", fontsize=7, color=MUTED, ha="right", va="center")
    ax.text(3.35, -0.05, "defence", fontsize=7, color=MUTED, ha="right", va="center")
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.01, label=cbar_label)
    ax.set(xlim=(-0.8, 9.8), ylim=(-0.7, 9), title=title)
    ax.axis("off")
    fig.savefig(path)
    plt.close(fig)


def score_boxplot(scores: pd.DataFrame, groups: pd.Series, path, title: str = "",
                  labels: dict[str, str] | None = None):
    labels = labels or {"Control": "Control", "Case": "Case"}
    cols = list(scores.columns)
    fig, ax = plt.subplots(figsize=(0.62 * len(cols) + 2, 4.4))
    pos = np.arange(len(cols))
    for i, grp in enumerate(("Control", "Case")):
        idx = groups[groups == grp].index.intersection(scores.index)
        data = [scores.loc[idx, c].dropna() for c in cols]
        bp = ax.boxplot(data, positions=pos + (i - 0.5) * 0.36, widths=0.3, patch_artist=True,
                        showfliers=False, medianprops={"color": INK, "lw": 1.2},
                        whiskerprops={"color": MUTED}, capprops={"color": MUTED})
        for b in bp["boxes"]:
            b.set(facecolor=GROUP_COLORS[grp], edgecolor="white")
        ax.plot([], [], color=GROUP_COLORS[grp], lw=8, label=f"{labels[grp]} (n={len(idx)})")
    ax.set_xticks(pos, [score_label(c) for c in cols], rotation=35, ha="right")
    ax.axhline(0, c=MUTED, lw=0.6, ls=":")
    ax.set(ylabel="score (z vs. control)", title=title)
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(path)
    plt.close(fig)


def _cell_heatmap(mat: pd.DataFrame, path, title: str, cbar: str, stars: pd.DataFrame | None = None,
                  vmax: float | None = None, row_labels=None, col_rotation=40, row_spans: bool = False,
                  figsize=None):
    vmax = vmax or max(0.5, float(np.nanmax(np.abs(mat.values))) if np.isfinite(mat.values).any() else 1)
    h = figsize or (0.55 * mat.shape[1] + 3.2, 0.2 * mat.shape[0] + 1.8)
    fig, ax = plt.subplots(figsize=h)
    im = ax.imshow(mat.values.astype(float), aspect="auto", cmap=DIVERGING, vmin=-vmax, vmax=vmax,
                   interpolation="nearest")
    ax.set_xticks(range(mat.shape[1]), mat.columns, rotation=col_rotation, ha="right" if col_rotation else "center",
                  fontsize=8)
    ax.set_yticks(range(mat.shape[0]), row_labels or mat.index, fontsize=7)
    ax.set_xticks(np.arange(-0.5, mat.shape[1]), minor=True)
    ax.set_yticks(np.arange(-0.5, mat.shape[0]), minor=True)
    ax.grid(which="minor", color="white", lw=1.2)
    ax.tick_params(which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    if stars is not None:
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                q = stars.iat[i, j]
                if pd.notna(q) and q < 0.05:
                    ax.text(j, i, "**" if q < 0.01 else "*", ha="center", va="center", fontsize=7,
                            color="white" if abs(mat.iat[i, j]) > 0.6 * vmax else INK)
    if row_spans:
        ax.yaxis.tick_right()
        _label_modules(ax, list(mat.index))
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.12 if row_spans else 0.02, label=cbar)
    fig.savefig(path)
    plt.close(fig)


def atlas_gene_heatmap(g: pd.DataFrame, q: pd.DataFrame, path, title: str = ""):
    """Genes (grouped by module) x cohort strata, Hedges' g; * FDR<0.05, ** FDR<0.01."""
    genes = _ordered_genes(g.index)
    _cell_heatmap(g.loc[genes], path, title, "Hedges' g (case vs control)", q.loc[genes], vmax=1.5,
                  row_spans=True)


def atlas_score_heatmap(d: pd.DataFrame, q: pd.DataFrame, path, title: str = ""):
    rows = list(d.index)
    _cell_heatmap(d, path, title, "Hedges' g (case vs control)", q, vmax=1.5,
                  row_labels=[score_label(r) for r in rows])


def correlation_heatmap(scores: pd.DataFrame, path, title: str = ""):
    c = scores.corr(method="spearman")
    labels = [score_label(x) for x in c.index]
    c.index, c.columns = labels, labels
    _cell_heatmap(c, path, title, "Spearman rho", vmax=1, figsize=(0.42 * len(c) + 3.5, 0.36 * len(c) + 1.5))


def biomarker_heatmap(corr: pd.DataFrame, path, title: str = ""):
    """Scores x biomarkers Spearman rho from the long table produced by stats.correlate."""
    rho = corr.pivot(index="score", columns="target", values="spearman_rho")
    q = corr.pivot(index="score", columns="target", values="fdr").reindex_like(rho)
    _cell_heatmap(rho, path, title, "Spearman rho", q, vmax=1, row_labels=[score_label(r) for r in rho.index],
                  col_rotation=0, figsize=(1.1 * rho.shape[1] + 3.2, 0.32 * rho.shape[0] + 1.6))


def paired_plot(scores: pd.DataFrame, groups: pd.Series, pairs: pd.Series, cols: list[str], path,
                case: str, control: str, title: str = ""):
    """Spaghetti plots of selected scores, one line per subject (control -> case timepoint)."""
    fig, axes = plt.subplots(1, len(cols), figsize=(2.4 * len(cols) + 0.4, 3.6), squeeze=False)
    df = pd.DataFrame({"group": groups, "pair": pairs}).dropna()
    for ax, col in zip(axes[0], cols, strict=False):
        a = df[df.group == "Control"].reset_index(names="s").drop_duplicates("pair").set_index("pair")["s"]
        b = df[df.group == "Case"].reset_index(names="s").drop_duplicates("pair").set_index("pair")["s"]
        shared = a.index.intersection(b.index)
        ya, yb = scores.loc[a.loc[shared], col].values, scores.loc[b.loc[shared], col].values
        for y0, y1 in zip(ya, yb, strict=True):
            ax.plot([0, 1], [y0, y1], color="#c9c8c2", lw=0.8)
        ax.plot([0, 1], [np.nanmean(ya), np.nanmean(yb)], color="#2a78d6", lw=2.2, marker="o", ms=6)
        ax.set_xticks([0, 1], [control, case])
        ax.set_xlim(-0.3, 1.3)
        ax.set_title(score_label(col), fontsize=9)
    axes[0][0].set_ylabel("score (z vs. reference)")
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
