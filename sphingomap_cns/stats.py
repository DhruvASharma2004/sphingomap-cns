"""Differential expression, effect sizes, meta-analysis and correlation."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def bh_fdr(pvalues) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (NaNs preserved)."""
    p = np.asarray(pvalues, dtype=float)
    out = np.full(p.shape, np.nan)
    mask = ~np.isnan(p)
    pv = p[mask]
    n = pv.size
    if n == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order] * n / np.arange(1, n + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adj = np.empty(n)
    adj[order] = np.clip(ranked, 0, 1)
    out[mask] = adj
    return out


def hedges_g(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Bias-corrected standardised mean difference (x - y) and its sampling variance."""
    n1, n2 = len(x), len(y)
    if n1 < 2 or n2 < 2:
        return np.nan, np.nan
    sp = np.sqrt(((n1 - 1) * np.var(x, ddof=1) + (n2 - 1) * np.var(y, ddof=1)) / (n1 + n2 - 2))
    if sp == 0:
        return np.nan, np.nan
    j = 1 - 3 / (4 * (n1 + n2) - 9)
    g = j * (np.mean(x) - np.mean(y)) / sp
    var = (n1 + n2) / (n1 * n2) + g ** 2 / (2 * (n1 + n2))
    return g, var


def differential_expression(expr: pd.DataFrame, groups: pd.Series, covariates: pd.DataFrame | None = None,
                            case: str = "Case", control: str = "Control") -> pd.DataFrame:
    """Case-vs-control linear model per gene: y ~ group (+ covariates).

    ``log2FC`` is the covariate-adjusted group coefficient on the log2 scale.
    Without covariates this is Student's t-test. ``hedges_g`` is the standardised
    difference: plain Hedges' g without covariates, or the covariate-adjusted
    equivalent (from the model t-statistic) when covariates are used; it feeds the
    meta-analysis. A Mann-Whitney U p-value is reported alongside as a robustness check.
    """
    samples = groups[groups.isin([case, control])].index.intersection(expr.columns)
    g = groups.loc[samples]
    X = [np.ones(len(samples)), (g == case).astype(float).values]
    cov_names: list[str] = []
    if covariates is not None and not covariates.empty:
        c = covariates.reindex(samples)
        for col in c.columns:
            X.append(c[col].values.astype(float))
            cov_names.append(col)
    X = np.column_stack(X)
    Y = expr.loc[:, samples].to_numpy(dtype=float)
    n, p = X.shape
    rows = []
    xtx_inv = np.linalg.pinv(X.T @ X)
    is_case = (g == case).values
    for i, gene in enumerate(expr.index):
        y = Y[i]
        ok = ~np.isnan(y)
        a, b = y[ok & is_case], y[ok & ~is_case]
        if len(a) < 3 or len(b) < 3 or np.nanvar(y) == 0:
            rows.append((gene, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, len(a), len(b)))
            continue
        if ok.all():
            Xi, inv = X, xtx_inv
        else:
            Xi = X[ok]
            inv = np.linalg.pinv(Xi.T @ Xi)
        beta = inv @ Xi.T @ y[ok]
        resid = y[ok] - Xi @ beta
        dof = ok.sum() - p
        s2 = resid @ resid / dof if dof > 0 else np.nan
        se = np.sqrt(s2 * inv[1, 1])
        t = beta[1] / se if se > 0 else np.nan
        pval = 2 * stats.t.sf(abs(t), dof) if np.isfinite(t) else np.nan
        _, pmw = stats.mannwhitneyu(a, b, alternative="two-sided")
        if len(cov_names) and np.isfinite(t):
            # covariate-adjusted standardised difference from the model t-statistic
            n1, n2 = len(a), len(b)
            hg = (1 - 3 / (4 * (n1 + n2) - 9)) * t * np.sqrt(1 / n1 + 1 / n2)
            hv = (n1 + n2) / (n1 * n2) + hg ** 2 / (2 * (n1 + n2))
        else:
            hg, hv = hedges_g(a, b)
        rows.append((gene, beta[1], a.mean(), b.mean(), t, pval, pmw, hg, hv, len(a), len(b)))
    res = pd.DataFrame(rows, columns=["gene", "log2FC", "mean_case", "mean_control", "t", "p",
                                      "p_mannwhitney", "hedges_g", "g_var", "n_case", "n_control"]).set_index("gene")
    res["fdr"] = bh_fdr(res["p"])
    res["fdr_mannwhitney"] = bh_fdr(res["p_mannwhitney"])
    res.attrs["covariates"] = cov_names
    return res.sort_values("p")


def paired_differential_expression(expr: pd.DataFrame, groups: pd.Series, pairs: pd.Series,
                                   case: str, control: str) -> pd.DataFrame:
    """Within-subject comparison (e.g. week 24 vs baseline): paired t + Wilcoxon."""
    df = pd.DataFrame({"group": groups, "pair": pairs}).dropna()
    a = df[df.group == case].reset_index(names="sample").drop_duplicates("pair").set_index("pair")["sample"]
    b = df[df.group == control].reset_index(names="sample").drop_duplicates("pair").set_index("pair")["sample"]
    shared = a.index.intersection(b.index)
    if len(shared) < 3:
        raise ValueError(f"Only {len(shared)} complete pairs for {case} vs {control}; need at least 3")
    xa = expr.loc[:, a.loc[shared].tolist()].to_numpy(dtype=float)
    xb = expr.loc[:, b.loc[shared].tolist()].to_numpy(dtype=float)
    rows = []
    for i, gene in enumerate(expr.index):
        d = xa[i] - xb[i]
        d = d[~np.isnan(d)]
        if len(d) < 3 or np.allclose(d, 0):
            rows.append((gene, np.nan, np.nan, np.nan, np.nan, len(d)))
            continue
        _, p = stats.ttest_1samp(d, 0)
        _, pw = stats.wilcoxon(d)
        dz = d.mean() / d.std(ddof=1) if d.std(ddof=1) > 0 else np.nan
        rows.append((gene, d.mean(), dz, p, pw, len(d)))
    res = pd.DataFrame(rows, columns=["gene", "log2FC", "cohens_dz", "p", "p_wilcoxon", "n_pairs"])
    res = res.set_index("gene")
    res["fdr"] = bh_fdr(res["p"])
    res["fdr_wilcoxon"] = bh_fdr(res["p_wilcoxon"])
    res.attrs["n_pairs"] = len(shared)
    return res.sort_values("p")


def random_effects_meta(effects: pd.DataFrame, variances: pd.DataFrame, min_studies: int = 2) -> pd.DataFrame:
    """DerSimonian-Laird random-effects meta-analysis, one row per gene.

    ``effects``/``variances`` are genes x studies tables of Hedges' g and its variance.
    """
    rows = []
    for gene in effects.index:
        g = effects.loc[gene].to_numpy(dtype=float)
        v = variances.loc[gene].to_numpy(dtype=float)
        ok = np.isfinite(g) & np.isfinite(v) & (v > 0)
        g, v = g[ok], v[ok]
        k = len(g)
        if k < min_studies:
            rows.append((gene, np.nan, np.nan, np.nan, np.nan, np.nan, k))
            continue
        w = 1 / v
        fixed = (w * g).sum() / w.sum()
        q = (w * (g - fixed) ** 2).sum()
        c = w.sum() - (w ** 2).sum() / w.sum()
        tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
        wr = 1 / (v + tau2)
        est = (wr * g).sum() / wr.sum()
        se = np.sqrt(1 / wr.sum())
        z = est / se
        p = 2 * stats.norm.sf(abs(z))
        i2 = max(0.0, (q - (k - 1)) / q) if q > 0 else 0.0
        rows.append((gene, est, est - 1.96 * se, est + 1.96 * se, p, i2, k))
    res = pd.DataFrame(rows, columns=["gene", "g_meta", "ci_low", "ci_high", "p", "I2", "k"]).set_index("gene")
    res["fdr"] = bh_fdr(res["p"])
    return res


def correlate(scores: pd.DataFrame, targets: pd.DataFrame, min_n: int = 8) -> pd.DataFrame:
    """Spearman correlation of every score with every numeric target (long format, FDR)."""
    rows = []
    for s in scores.columns:
        for t in targets.columns:
            df = pd.concat([scores[s], pd.to_numeric(targets[t], errors="coerce")], axis=1).dropna()
            if len(df) < min_n or df.iloc[:, 0].nunique() < 3 or df.iloc[:, 1].nunique() < 3:
                continue
            rho, p = stats.spearmanr(df.iloc[:, 0], df.iloc[:, 1])
            rows.append((s, t, len(df), rho, p))
    res = pd.DataFrame(rows, columns=["score", "target", "n", "spearman_rho", "p"])
    res["fdr"] = bh_fdr(res["p"]) if len(res) else []
    return res.sort_values("p")
