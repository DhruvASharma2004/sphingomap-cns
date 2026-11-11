"""Normalisation, sample grouping and covariate parsing."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------- normalisation


def log_cpm(counts: pd.DataFrame, prior: float = 1.0) -> pd.DataFrame:
    """log2 counts-per-million from a full (all-genes) raw count matrix."""
    lib = counts.sum(axis=0).replace(0, np.nan)
    return np.log2(counts.div(lib, axis=1) * 1e6 + prior)


def ensure_log2(expr: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Microarray tables are sometimes linear-scale (e.g. MAS5). Log2 them if so."""
    vals = expr.to_numpy(dtype=float)
    q99 = np.nanpercentile(vals, 99) if np.isfinite(vals).any() else 0
    if q99 > 100:
        return np.log2(expr.clip(lower=1)), True
    return expr, False


def expressed_genes(expr: pd.DataFrame, platform: str) -> pd.Index:
    """Genes with usable signal.

    RNA-seq: CPM >= 1 (log2CPM >= 1 with prior 1) in at least 20% of samples.
    Microarray: mean signal above the 25th percentile of all gene means.
    """
    if platform == "rnaseq":
        keep = (expr >= 1).mean(axis=1) >= 0.2
    else:
        means = expr.mean(axis=1)
        keep = means > means.quantile(0.25)
    return expr.index[keep]


# ----------------------------------------------------------------------------- grouping


def _values_text(ann: pd.DataFrame, field: str | None = None) -> pd.Series:
    """Text to match per sample: one annotation column if ``field`` is given, else all values joined."""
    if field:
        cols = {c.lower(): c for c in ann.columns}
        if field.lower() not in cols:
            raise KeyError(f"Annotation column '{field}' not found; have: {list(ann.columns)}")
        return ann[cols[field.lower()]].astype(str).str.strip()
    return ann.astype(str).agg(" | ".join, axis=1)


def assign_groups(ann: pd.DataFrame, case: str, control: str, exclude: str | None = None,
                  field: str | None = None) -> pd.Series:
    """Label each sample Case / Control / NaN by regex over its annotation values.

    Samples matching both patterns are ambiguous and dropped.
    """
    text = _values_text(ann, field)
    is_case = text.str.contains(case, flags=re.I, regex=True)
    is_ctrl = text.str.contains(control, flags=re.I, regex=True)
    g = pd.Series(np.nan, index=ann.index, dtype=object)
    g[is_case & ~is_ctrl] = "Case"
    g[is_ctrl & ~is_case] = "Control"
    if exclude:
        g[_values_text(ann).str.contains(exclude, flags=re.I, regex=True)] = np.nan
    return g


def assign_strata(ann: pd.DataFrame, strata: dict[str, str] | None, field: str | None = None) -> pd.Series:
    """First matching stratum label per sample (NaN if none match)."""
    if not strata:
        return pd.Series("All", index=ann.index)
    text = _values_text(ann, field)
    out = pd.Series(np.nan, index=ann.index, dtype=object)
    for label, pat in strata.items():
        hit = text.str.contains(pat, flags=re.I, regex=True) & out.isna()
        out[hit] = label
    return out


# ----------------------------------------------------------------------------- covariates

_SEX_KEYS = re.compile(r"^(sex|gender)\b", re.I)
_AGE_KEYS = re.compile(r"\bage\b", re.I)


def parse_covariates(ann: pd.DataFrame) -> pd.DataFrame:
    """Extract sex (0/1) and age (years) from free-text annotation columns if present."""
    cov = pd.DataFrame(index=ann.index)
    for col in ann.columns:
        if "sex_male" not in cov and _SEX_KEYS.search(col):
            v = ann[col].astype(str).str.strip().str.lower()
            sex = v.map(lambda s: 1.0 if s.startswith(("m", "1")) else 0.0 if s.startswith(("f", "2", "0"))
                        else np.nan)
            if sex.notna().mean() > 0.5:
                cov["sex_male"] = sex
        if "age" not in cov and _AGE_KEYS.search(col):
            num = pd.to_numeric(ann[col].astype(str).str.extract(r"(\d+(?:\.\d+)?)")[0], errors="coerce")
            if num.notna().mean() > 0.5 and num.between(0, 120).mean() > 0.5:
                cov["age"] = num
    return cov


def usable_covariates(cov: pd.DataFrame, samples: pd.Index, min_coverage: float = 0.9) -> pd.DataFrame:
    """Covariates that are present for >= 90% of samples and vary; missing values mean-imputed."""
    c = cov.reindex(samples)
    keep = [k for k in c.columns if c[k].notna().mean() >= min_coverage and c[k].nunique() > 1]
    c = c[keep]
    return c.fillna(c.mean())


def one_per_subject(samples: pd.Index, ann: pd.DataFrame, field: str | None) -> pd.Index:
    """Keep the first sample of each donor (avoids counting repeat libraries / regions twice)."""
    if not field:
        return samples
    cols = {c.lower(): c for c in ann.columns}
    col = cols.get(field.lower())
    if col is None:
        return samples
    subj = ann.loc[samples, col].astype(str)
    return pd.Index(subj[~subj.duplicated()].index)
