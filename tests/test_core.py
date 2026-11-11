import gzip
import json

import numpy as np
import pandas as pd
import pytest

from sphingomap_cns import geo
from sphingomap_cns.design import (
    assign_groups,
    assign_strata,
    ensure_log2,
    log_cpm,
    one_per_subject,
    parse_covariates,
    usable_covariates,
)
from sphingomap_cns.genesets import (
    ALIASES,
    COMPOSITE_INDICES,
    FOCUS_GENES,
    MODULES,
    PATHWAY_LAYOUT,
    RHEOSTAT,
    all_genes,
)
from sphingomap_cns.registry import COHORTS
from sphingomap_cns.scores import module_scores
from sphingomap_cns.stats import (
    bh_fdr,
    correlate,
    differential_expression,
    hedges_g,
    paired_differential_expression,
    random_effects_meta,
)

SERIES = """!Series_title\t"Test"
!Sample_title\t"ALS_1"\t"CTRL_1"\t"ALS_2"\t"OND_1"
!Sample_geo_accession\t"GSM1"\t"GSM2"\t"GSM3"\t"GSM4"
!Sample_source_name_ch1\t"Spinal Cord Cervical"\t"Spinal Cord Cervical"\t"Cortex Motor Lateral"\t"Cortex Motor Lateral"
!Sample_characteristics_ch1\t"project: NYGC ALS Consortium"\t"project: NYGC ALS Consortium"\t"project: NYGC ALS Consortium"\t"project: NYGC ALS Consortium"
!Sample_characteristics_ch1\t"tissue: Spinal Cord Cervical"\t"tissue: Spinal Cord Cervical"\t"tissue: Cortex Motor Lateral"\t"tissue: Cortex Motor Lateral"
!Sample_characteristics_ch1\t"subject id: S1"\t"subject id: S2"\t"subject id: S1"\t"subject id: S3"
!Sample_characteristics_ch1\t"group: ALS Spectrum MND"\t"group: Non-Neurological Control"\t"group: ALS Spectrum MND"\t"group: ALS Spectrum MND, Other Neurological Disorders"
!Sample_characteristics_ch1\t"sex: Male"\t"sex: Female"\t"sex: Female"\t"sex: Male"
!Sample_characteristics_ch1\t"age at death: 61"\t"age at death: 70"\t"age at death: 55 years"\t"age at death: 80"
!Sample_platform_id\t"GPL1"\t"GPL1"\t"GPL1"\t"GPL1"
!series_matrix_table_begin
"ID_REF"\t"GSM1"\t"GSM2"\t"GSM3"\t"GSM4"
"p1"\t200\t150\t180\t120
"p2"\t50\t60\t40\t70
"p3"\t1000\t900\t800\t950
"p4"\t5\t6\t5\t7
!series_matrix_table_end
"""

PLATFORM = """^PLATFORM = GPL1
!platform_table_begin
ID\tGene title\tGene symbol
p1\tsphingomyelin phosphodiesterase 1\tSMPD1
p2\tceramide synthase 2\tLASS2
p3\tglutathione peroxidase 4\tGPX4
p4\tambiguous\tA /// B
p5\tsecond SMPD1 probe\tSMPD1
!platform_table_end
"""


@pytest.fixture
def series_file(tmp_path):
    p = tmp_path / "GSE1_series_matrix.txt.gz"
    with gzip.open(p, "wt") as fh:
        fh.write(SERIES)
    return p


def test_genesets_consistent():
    genes = all_genes()
    assert len(genes) == len(set(genes)), "a gene is in two modules"
    for up, down in COMPOSITE_INDICES.values():
        assert set(up) <= set(genes) and set(down) <= set(genes)
        assert not set(up) & set(down)
    assert not set(RHEOSTAT["pro_survival"]) & set(RHEOSTAT["pro_ceramide"])
    assert set(PATHWAY_LAYOUT) <= set(genes)
    assert set(FOCUS_GENES) <= set(genes)
    assert all(v in genes for v in ALIASES.values())
    assert all(k not in genes for k in ALIASES)
    assert {m["kind"] for m in MODULES.values()} == {"sphingolipid", "context"}


def test_registry_patterns_compile():
    import re
    for cid, cfg in COHORTS.items():
        assert cfg["platform"] in {"rnaseq", "array"}
        assert cfg["platform"] == "rnaseq" or cfg.get("gpl"), cid
        for case, ctrl in cfg["contrasts"].values():
            re.compile(case)
            re.compile(ctrl)
        for pat in (cfg.get("strata") or {}).values():
            re.compile(pat)


def test_stub():
    assert geo._stub("GSE5281") == "GSE5nnn"
    assert geo._stub("GSE153960") == "GSE153nnn"
    assert geo._stub("GSE112") == "GSEnnn"
    assert geo._stub("GPL570") == "GPLnnn"
    assert geo._stub("GPL10558") == "GPL10nnn"


def test_parse_series_matrix(series_file):
    ann, expr = geo.parse_series_matrix(series_file)
    assert list(ann.index) == ["GSM1", "GSM2", "GSM3", "GSM4"]
    assert ann.loc["GSM2", "group"] == "Non-Neurological Control"
    assert ann.loc["GSM3", "source"] == "Cortex Motor Lateral"
    assert expr.shape == (4, 4) and expr.loc["p3", "GSM1"] == 1000


def test_platform_and_probe_collapse(tmp_path, series_file):
    pf = tmp_path / "GPL1.annot.gz"
    with gzip.open(pf, "wt") as fh:
        fh.write(PLATFORM)
    m = geo.parse_platform(pf)
    assert "p4" not in m.index  # multi-gene probe dropped
    _, expr = geo.parse_series_matrix(series_file)
    genes = geo.probes_to_genes(expr, m)
    assert {"SMPD1", "CERS2", "GPX4"} == set(genes.index)  # LASS2 -> CERS2
    logged, did = ensure_log2(genes)
    assert did and logged.max().max() < 12


def test_ncbi_counts(tmp_path):
    counts = pd.DataFrame({"GSM1": [10, 0, 5], "GSM2": [20, 3, 0]}, index=pd.Index(["6609", "29956", "999"],
                                                                                    name="GeneID"))
    counts.to_csv(tmp_path / "c.tsv", sep="\t")
    pd.DataFrame({"GeneID": ["6609", "29956", "999"], "Symbol": ["SMPD1", "LASS2", "FOO"]}).to_csv(
        tmp_path / "a.tsv", sep="\t", index=False)
    out = geo.load_ncbi_counts(tmp_path / "c.tsv", tmp_path / "a.tsv")
    assert out.loc["CERS2", "GSM2"] == 3 and out.loc["SMPD1", "GSM1"] == 10
    cpm = log_cpm(out)
    assert np.isclose((2 ** cpm - 1).sum().values, 1e6).all()


def test_grouping_and_covariates(series_file):
    ann, _ = geo.parse_series_matrix(series_file)
    cfg = COHORTS["GSE153960"]
    case, ctrl = cfg["contrasts"]["ALS"]
    g = assign_groups(ann, case, ctrl, cfg.get("exclude"), cfg["group_field"])
    assert g["GSM1"] == "Case" and g["GSM2"] == "Control" and g["GSM3"] == "Case"
    assert pd.isna(g["GSM4"])  # ALS + other neurological diagnosis left out
    # matching over all fields would make every sample 'ALS' via the project name
    g_all = assign_groups(ann, r"\bALS\b", r"Non-Neurological Control")
    assert pd.isna(g_all["GSM2"])
    st = assign_strata(ann, cfg["strata"], cfg["strata_field"])
    assert st["GSM1"] == "Spinal cord (cervical)" and st["GSM3"] == "Motor cortex (lateral)"
    assert list(one_per_subject(pd.Index(["GSM1", "GSM2", "GSM3"]), ann, "subject id")) == ["GSM1", "GSM2"]
    cov = parse_covariates(ann)
    assert list(cov["sex_male"]) == [1, 0, 0, 1] and list(cov["age"]) == [61, 70, 55, 80]
    assert set(usable_covariates(cov, ann.index).columns) == {"sex_male", "age"}


def test_group_keys_not_matched():
    """A characteristics *key* containing 'control' must not make every sample a control."""
    ann = pd.DataFrame({"case/control status": ["ALS", "healthy control"]}, index=["a", "b"])
    g = assign_groups(ann, r"\bALS\b", r"control")
    assert g["a"] == "Case" and g["b"] == "Control"


def test_bh_and_hedges():
    adj = bh_fdr([0.01, 0.04, 0.03, np.nan, 0.5])
    assert np.isnan(adj[3]) and np.allclose(adj[[0, 1, 2, 4]], [0.04, 0.0533333, 0.0533333, 0.5])
    g, v = hedges_g(np.array([1, 2, 3, 4.0]), np.array([1, 2, 3, 4.0]))
    assert g == 0 and v > 0


def _toy(n=30, seed=0, effect=1.0):
    rng = np.random.default_rng(seed)
    genes = ["SMPD1", "GPX4", "CERS2", "CERS5", "CERS6", "SMPD3", "SGMS1", "SGMS2"] + [f"X{i}" for i in range(20)]
    x = rng.normal(8, 0.5, (len(genes), 2 * n))
    x[0, :n] += effect
    x[1, :n] -= effect
    cols = [f"s{i}" for i in range(2 * n)]
    groups = pd.Series(["Case"] * n + ["Control"] * n, index=cols)
    return pd.DataFrame(x, index=genes, columns=cols), groups


def test_differential_expression_recovers_effects():
    expr, groups = _toy()
    de = differential_expression(expr, groups)
    assert de.loc["SMPD1", "log2FC"] == pytest.approx(1.0, abs=0.3)
    assert de.loc["GPX4", "log2FC"] == pytest.approx(-1.0, abs=0.3)
    assert de.loc["SMPD1", "fdr"] < 1e-6 and de.loc["X3", "fdr"] > 0.05
    cov = pd.DataFrame({"age": np.random.default_rng(1).normal(60, 10, len(groups))}, index=groups.index)
    de2 = differential_expression(expr, groups, cov)
    assert de2.attrs["covariates"] == ["age"] and de2.loc["SMPD1", "fdr"] < 1e-6


def test_paired():
    rng = np.random.default_rng(3)
    n = 12
    subj = rng.normal(8, 1, (5, n))
    pre = subj + rng.normal(0, 0.1, (5, n))
    post = subj + rng.normal(0, 0.1, (5, n))
    post[0] += 0.5
    cols = [f"p{i}_pre" for i in range(n)] + [f"p{i}_post" for i in range(n)]
    expr = pd.DataFrame(np.hstack([pre, post]), index=["FOXP3", "A", "B", "C", "D"], columns=cols)
    groups = pd.Series(["Control"] * n + ["Case"] * n, index=cols)
    pairs = pd.Series([c.split("_")[0] for c in cols], index=cols)
    res = paired_differential_expression(expr, groups, pairs, "Case", "Control")
    assert res.attrs["n_pairs"] == n
    assert res.loc["FOXP3", "log2FC"] == pytest.approx(0.5, abs=0.1) and res.loc["FOXP3", "fdr"] < 1e-4
    # an unpaired test misses this within-subject shift
    assert differential_expression(expr, groups).loc["FOXP3", "p"] > 0.05


def test_meta_analysis():
    eff = pd.DataFrame({"a": [0.8, 0.0], "b": [0.7, 0.05], "c": [0.9, -0.05]}, index=["G1", "G2"])
    var = pd.DataFrame(0.05, index=eff.index, columns=eff.columns)
    m = random_effects_meta(eff, var)
    assert m.loc["G1", "g_meta"] == pytest.approx(0.8, abs=0.05) and m.loc["G1", "fdr"] < 0.001
    assert m.loc["G2", "fdr"] > 0.5 and m.loc["G1", "k"] == 3


def test_scores_and_correlate():
    expr, groups = _toy()
    scores, used = module_scores(expr, reference=list(groups[groups == "Control"].index))
    assert "sphingomyelin_cycle" in scores and "cpa_index" in scores
    case = groups[groups == "Case"].index
    assert scores.loc[case, "cpa_index"].mean() > 0.5 # SMPD1 up, GPX4 down
    bm = pd.DataFrame({"HNE": scores["cpa_index"] + np.random.default_rng(2).normal(0, 0.1, len(scores))})
    c = correlate(scores[["cpa_index"]], bm)
    assert c.iloc[0].spearman_rho > 0.9


def test_demo_end_to_end(tmp_path):
    from sphingomap_cns.cli import main
    assert main(["demo", "-o", str(tmp_path)]) == 0
    atlas = tmp_path / "atlas"
    for f in ("ATLAS_REPORT.md", "atlas.html", "atlas_meta_analysis.csv", "figures/atlas_genes.png",
              "figures/pathway_meta_ALS_CNS.png"):
        assert (atlas / f).exists(), f
    meta = pd.read_csv(atlas / "atlas_meta_analysis.csv", index_col=0)
    als = meta[meta.contrast == "ALS CNS"]
    # planted effects are recovered in the right direction
    assert als.loc["SMPD1", "g_meta"] > 0.3 and als.loc["SMPD1", "fdr"] < 0.05
    assert als.loc["NEFL", "g_meta"] < -0.5
    runs = pd.read_csv(atlas / "atlas_runs.csv")
    assert (runs.status == "ok").sum() == 8 and (runs.status == "skipped").sum() == 2
    trial = json.loads((tmp_path / "trial_active" / "summary.json").read_text())
    assert trial["design"] == "paired" and trial["n_pairs"] == 24
    assert "FOXP3" in trial["up"] and "SMPD1" in trial["down"]
    cpa = next(s for s in trial["scores"] if s["score"] == "cpa_index")
    assert cpa["mean_difference"] < 0 and cpa["fdr"] < 0.05
    placebo = json.loads((tmp_path / "trial_placebo" / "summary.json").read_text())
    assert placebo["n_significant"] <= 2
    html = (atlas / "atlas.html").read_text()
    assert "const D = {" in html and "data:image/png;base64" in html


def test_pseudobulk(tmp_path):
    from sphingomap_cns.userdata import pseudobulk
    rng = np.random.default_rng(0)
    cells = pd.DataFrame({"sample": np.repeat(["S1", "S2"], 60), "cell_type": np.tile(["Treg", "Mono"], 60),
                          "FOXP3": rng.normal(5, 1, 120), "CD14": rng.normal(3, 1, 120)})
    cells.to_csv(tmp_path / "cells.csv", index=False)
    pd.DataFrame({"sample": ["S1", "S2"], "timepoint": ["Baseline", "Week24"]}).to_csv(tmp_path / "md.csv",
                                                                                         index=False)
    pseudobulk(tmp_path / "cells.csv", tmp_path / "pb", celltype_col="cell_type", metadata=tmp_path / "md.csv")
    e = pd.read_csv(tmp_path / "pb_expression.tsv", sep="\t", index_col=0)
    s = pd.read_csv(tmp_path / "pb_samples.csv")
    assert e.shape == (2, 4) and set(s.cell_type) == {"Treg", "Mono"} and set(s.timepoint) == {"Baseline", "Week24"}


def test_download_rejects_html(tmp_path, monkeypatch):
    import io as _io
    import urllib.request

    class R(_io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: R(b"<!DOCTYPE html><html>nope</html>"))
    with pytest.raises(OSError, match="HTML"):
        geo.download("https://example.org/x.gz", tmp_path / "x.gz")
    assert not (tmp_path / "x.gz").exists()
    (tmp_path / "y.gz").write_bytes(b"<!DOCTYPE html>")  # poisoned cache entry gets re-fetched
    with pytest.raises(OSError):
        geo.download("https://example.org/y.gz", tmp_path / "y.gz")
