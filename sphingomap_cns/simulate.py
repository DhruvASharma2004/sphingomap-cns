"""Synthetic data for tests, CI and offline demos.

Everything here is simulated. The planted effects are chosen so you can see that
the pipeline recovers them; they are NOT biological findings and must never be
presented as such.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .genesets import all_genes

# Planted case-control shifts (log2 units) per simulated compartment.
PLANTED_CNS = {"SMPD1": 0.7, "SMPD3": 0.6, "NSMAF": 0.4, "CERS6": 0.5, "CERS2": 0.3, "ACSL4": 0.5,
               "ALOX5": 0.6, "CYBB": 0.8, "CD68": 0.9, "TREM2": 0.8, "AIF1": 0.6, "TYROBP": 0.7,
               "GPX4": -0.5, "SLC7A11": -0.4, "SGMS1": -0.5, "NEFL": -1.0, "NEFH": -0.9, "NEFM": -0.8,
               "S1PR1": -0.4, "SPHK1": 0.4}
PLANTED_BLOOD = {"TNF": 0.4, "IL1B": 0.5, "SMPD1": 0.3, "CD14": 0.4, "FOXP3": -0.4, "IL2RA": -0.3,
                 "CTLA4": -0.3, "ALOX5": 0.3, "GPX4": -0.2}

SIM_REGISTRY: dict[str, dict] = {
    "SIM-CNS-1": {"title": "Simulated post-mortem CNS RNA-seq (ALS, FTD, controls)", "reference": "synthetic",
                  "platform": "rnaseq", "compartment": "CNS",
                  "contrasts": {"ALS": (r"\bALS\b", r"Non-Neurological Control"),
                                "FTD": (r"\bFTLD\b", r"Non-Neurological Control")},
                  "exclude": r"Other Neurological",
                  "strata": {"Spinal cord": r"spinal", "Motor cortex": r"motor cortex",
                             "Frontal cortex": r"frontal cortex"}},
    "SIM-CNS-2": {"title": "Simulated AD brain microarray", "reference": "synthetic", "platform": "array",
                  "compartment": "CNS", "contrasts": {"AD": (r"alzheimer", r"\bnormal\b")},
                  "strata": {"Hippocampus": r"hippocamp", "Entorhinal cortex": r"entorhinal"}},
    "SIM-CNS-3": {"title": "Simulated ALS spinal cord RNA-seq (second cohort)", "reference": "synthetic",
                  "platform": "rnaseq", "compartment": "CNS",
                  "contrasts": {"ALS": (r"\bALS\b", r"control")}, "strata": {"Spinal cord": r"spinal"}},
    "SIM-BLOOD": {"title": "Simulated ALS whole-blood microarray", "reference": "synthetic", "platform": "array",
                  "compartment": "Blood", "contrasts": {"ALS": (r"\bALS\b", r"\bCON\b")}},
}


def _expr(rng, genes, base, n, planted, scale, noise, donor=None):
    shift = np.array([planted.get(g, 0.0) for g in genes]) * scale
    m = base[:, None] + shift[:, None] + rng.normal(0, noise, (len(genes), n))
    if donor is not None:
        m = m + donor
    return m


def simulate_geo_cohorts(seed: int = 11) -> tuple[dict[str, dict], dict[str, dict]]:
    """Return (prepared cohorts, registry) in the same shape ``atlas.build_atlas`` uses for GEO."""
    rng = np.random.default_rng(seed)
    genes = all_genes() + [f"FILLER{i:03d}" for i in range(150)]
    prepared = {}

    # --- cohort 1: multi-region ALS/FTD RNA-seq --------------------------------
    rows, cols = [], []
    base = rng.uniform(2.5, 9, len(genes))
    gsm = 100000
    for tissue, groups in (("Spinal Cord, Cervical", {"ALS Spectrum MND": 34, "Non-Neurological Control": 14}),
                           ("Motor Cortex", {"ALS Spectrum MND": 36, "Non-Neurological Control": 16,
                                             "Other Neurological Disorders": 6}),
                           ("Frontal Cortex", {"ALS Spectrum MND": 30, "FTLD": 24,
                                               "Non-Neurological Control": 18})):
        scale = 1.0 if "Spinal" in tissue else 0.55
        for grp, n in groups.items():
            planted = PLANTED_CNS if grp in ("ALS Spectrum MND", "FTLD") else {}
            s = scale * (0.8 if grp == "FTLD" else 1.0)
            cols.append(_expr(rng, genes, base, n, planted, s, 0.55))
            for _ in range(n):
                gsm += 1
                rows.append({"sample": f"GSM{gsm}", "title": f"{tissue} {grp} {gsm}", "source": tissue,
                             "subject group": grp, "tissue": tissue, "sex": rng.choice(["Male", "Female"]),
                             "age at death": str(int(rng.integers(45, 85)))})
    ann = pd.DataFrame(rows).set_index("sample")
    prepared["SIM-CNS-1"] = {"expr": pd.DataFrame(np.hstack(cols), index=genes, columns=ann.index),
                             "ann": ann, "platform": "rnaseq", "scale": "simulated log2 CPM"}

    # --- cohort 2: AD microarray --------------------------------------------------
    rows, cols = [], []
    base = rng.uniform(5, 12, len(genes))
    for region in ("Hippocampus", "Entorhinal Cortex"):
        for grp, n in (("Alzheimer's Disease", 18), ("normal", 12)):
            cols.append(_expr(rng, genes, base, n, PLANTED_CNS if grp != "normal" else {}, 0.6, 0.45))
            for _ in range(n):
                gsm += 1
                rows.append({"sample": f"GSM{gsm}", "title": f"{region}_{grp}_{gsm}",
                             "source": f"brain, {region}", "organ region": region, "disease state": grp,
                             "Sex": rng.choice(["male", "female"]), "age": f"{int(rng.integers(65, 95))} years"})
    ann = pd.DataFrame(rows).set_index("sample")
    prepared["SIM-CNS-2"] = {"expr": pd.DataFrame(np.hstack(cols), index=genes, columns=ann.index),
                             "ann": ann, "platform": "array", "scale": "simulated log2 intensity"}

    # --- cohort 3: independent ALS spinal cord -----------------------------------
    rows, cols = [], []
    base = rng.uniform(2.5, 9, len(genes))
    for grp, n in (("ALS", 28), ("control", 12)):
        cols.append(_expr(rng, genes, base, n, PLANTED_CNS if grp == "ALS" else {}, 0.8, 0.6))
        for _ in range(n):
            gsm += 1
            rows.append({"sample": f"GSM{gsm}", "title": f"{grp}_SC_{gsm}", "source": "lumbar spinal cord",
                         "diagnosis": grp})
    ann = pd.DataFrame(rows).set_index("sample")
    prepared["SIM-CNS-3"] = {"expr": pd.DataFrame(np.hstack(cols), index=genes, columns=ann.index),
                             "ann": ann, "platform": "rnaseq", "scale": "simulated log2 CPM"}

    # --- cohort 4: blood -------------------------------------------------------------
    rows, cols = [], []
    base = rng.uniform(6, 13, len(genes))
    for grp, n in (("ALS", 70), ("CON", 50)):
        cols.append(_expr(rng, genes, base, n, PLANTED_BLOOD if grp == "ALS" else {}, 1.0, 0.4))
        for _ in range(n):
            gsm += 1
            rows.append({"sample": f"GSM{gsm}", "title": f"blood_{grp}_{gsm}", "source": "whole blood",
                         "diagnosis": grp, "gender": rng.choice(["M", "F"])})
    ann = pd.DataFrame(rows).set_index("sample")
    prepared["SIM-BLOOD"] = {"expr": pd.DataFrame(np.hstack(cols), index=genes, columns=ann.index),
                             "ann": ann, "platform": "array", "scale": "simulated log2 intensity"}
    return prepared, SIM_REGISTRY


def simulate_trial(outdir: str | Path, n_per_arm: int = 24, seed: int = 5) -> dict[str, Path]:
    """Longitudinal PBMC-style dataset: baseline vs week 24, active vs placebo, with lipid biomarkers.

    Active arm: Treg axis rises, myeloid activation / SMase / peroxidation genes fall; serum
    4-HNE, MDA and NfL track each subject's ceramide-peroxidation tilt. Purely synthetic.
    """
    rng = np.random.default_rng(seed)
    genes = all_genes() + [f"FILLER{i:03d}" for i in range(100)]
    base = rng.uniform(4, 11, len(genes))
    gi = {g: i for i, g in enumerate(genes)}
    up_t = {"FOXP3": 0.8, "IL2RA": 0.9, "CTLA4": 0.6, "IKZF2": 0.5, "TNFRSF18": 0.5, "IL10": 0.4}
    down_t = {"CD14": -0.4, "CD68": -0.4, "TNF": -0.5, "IL1B": -0.5, "SMPD1": -0.4, "NSMAF": -0.3,
              "SMPD3": -0.3, "ALOX5": -0.4, "CYBB": -0.4, "NCF1": -0.3, "CERS6": -0.3}
    cpa_genes_up = ["SMPD1", "SMPD3", "NSMAF", "CERS6", "ALOX5", "CYBB", "NCF1", "ACSL4"]
    rows, data = [], {}
    for arm in ("Active", "Placebo"):
        for p in range(n_per_arm):
            subj = f"{arm[0]}{p + 1:03d}"
            donor = rng.normal(0, 0.3, len(genes))
            tilt = rng.normal(0, 1)  # subject-level ceramide-peroxidation tilt
            for tp in ("Baseline", "Week24"):
                x = base + donor + rng.normal(0, 0.25, len(genes))
                for g in cpa_genes_up:
                    x[gi[g]] += 0.35 * tilt
                if arm == "Active" and tp == "Week24":
                    for g, v in {**up_t, **down_t}.items():
                        x[gi[g]] += v
                    tilt_tp = tilt - 0.8
                else:
                    tilt_tp = tilt
                sid = f"{subj}_{tp}"
                data[sid] = x
                rows.append({"sample": sid, "subject": subj, "arm": arm, "timepoint": tp,
                             "age": int(rng.integers(45, 75)) if tp == "Baseline" else None,
                             "sex": rng.choice(["M", "F"]),
                             "HNE_4_ng_ml": round(float(np.exp(1.2 + 0.25 * tilt_tp + rng.normal(0, 0.15))), 3),
                             "MDA_uM": round(float(np.exp(0.8 + 0.2 * tilt_tp + rng.normal(0, 0.15))), 3),
                             "NfL_pg_ml": round(float(np.exp(4.0 + 0.15 * tilt_tp + rng.normal(0, 0.2))), 1)})
    sheet = pd.DataFrame(rows)
    sheet["age"] = sheet.groupby("subject")["age"].transform("first")
    sheet["sex"] = sheet.groupby("subject")["sex"].transform("first")
    expr = pd.DataFrame(data, index=pd.Index(genes, name="gene")).round(4)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {"expression": out / "TRIAL_expression.tsv", "samples": out / "TRIAL_samples.csv"}
    expr.to_csv(paths["expression"], sep="\t")
    sheet.to_csv(paths["samples"], index=False)
    return paths
