"""Public neurodegeneration cohorts on NCBI GEO.

Each cohort describes how to download it and how to turn GEO sample
annotations into analysis groups. GEO annotations are free text, so groups and
tissues are assigned with case-insensitive regular expressions that are searched
across every sample annotation field (title, source, characteristics).

**Always check a cohort's labels before trusting results**::

    sphingomap-cns inspect GSE153960

prints every annotation field with its value counts, so the patterns below can
be adjusted if GEO wording differs from what is expected here. The pipeline
also writes ``sample_groups.csv`` for every run so the assignment can be audited.

Fields
------
platform      "rnaseq" (NCBI-generated raw counts) or "array" (series matrix + GPL annotation)
contrasts     {name: (case_pattern, control_pattern)}; samples matching neither are dropped
exclude       pattern; matching samples are removed before grouping
strata        {label: pattern}; one analysis per stratum (tissue / region). Samples
              matching no stratum are dropped. Omit for a single stratum.
compartment   "CNS" or "Blood" (for the atlas layout)
default       include in ``sphingomap-cns atlas`` when no cohort is named
"""
from __future__ import annotations

CONTROL = r"control|healthy|normal|\bCON\b|\bCTRL\b|\bHC\b"

COHORTS: dict[str, dict] = {
    "GSE153960": {
        "title": "NYGC ALS Consortium post-mortem CNS RNA-seq (ALS, FTD, controls)",
        "reference": "New York Genome Center ALS Consortium (GEO GSE153960)",
        "platform": "rnaseq",
        "compartment": "CNS",
        "contrasts": {
            "ALS": (r"\bALS\b|ALS[ -]Spectrum|\bMND\b|amyotrophic", r"Non-?Neurological Control"),
            "FTD": (r"\bFTLD\b|\bFTD\b|frontotemporal", r"Non-?Neurological Control"),
        },
        "exclude": r"Other Neurological",
        "strata": {
            "Spinal cord": r"spinal",
            "Motor cortex": r"motor cortex",
            "Frontal cortex": r"frontal cortex",
        },
        "default": True,
    },
    "GSE124439": {
        "title": "ALS frontal and motor cortex RNA-seq (Tam et al.)",
        "reference": "Tam O. H. et al., Cell Reports 29, 1164 (2019)",
        "platform": "rnaseq",
        "compartment": "CNS",
        "contrasts": {"ALS": (r"\bALS\b|\bMND\b|amyotrophic", CONTROL)},
        "strata": {"Motor cortex": r"motor cortex", "Frontal cortex": r"frontal cortex"},
        # Samples were sequenced by the NYGC consortium and are likely re-released
        # inside GSE153960; kept out of the default atlas to avoid double counting.
        "default": False,
        "note": "Probable sample overlap with GSE153960; run on its own, not in the meta-analysis.",
    },
    "GSE5281": {
        "title": "Alzheimer's disease, six brain regions, laser-captured neurons (Affymetrix U133 Plus 2)",
        "reference": "Liang W. S. et al., Physiol Genomics 28, 311 (2007)",
        "platform": "array",
        "gpl": "GPL570",
        "compartment": "CNS",
        "contrasts": {"AD": (r"alzheimer", r"\bnormal\b|control")},
        "strata": {
            "Entorhinal cortex": r"entorhinal",
            "Hippocampus": r"hippocamp",
            "Middle temporal gyrus": r"temporal gyrus",
            "Posterior cingulate": r"cingulate",
            "Superior frontal gyrus": r"frontal gyrus",
            "Primary visual cortex": r"visual cortex",
        },
        "default": True,
    },
    "GSE112676": {
        "title": "ALS whole blood, discovery set (Illumina HT-12 v3)",
        "reference": "van Rheenen W. et al., PLoS One 13, e0198874 (2018)",
        "platform": "array",
        "gpl": "GPL6947",
        "compartment": "Blood",
        "contrasts": {"ALS": (r"\bALS\b|amyotrophic", CONTROL)},
        "default": True,
    },
    "GSE112680": {
        "title": "ALS whole blood, replication set (Illumina HT-12 v4)",
        "reference": "van Rheenen W. et al., PLoS One 13, e0198874 (2018)",
        "platform": "array",
        "gpl": "GPL10558",
        "compartment": "Blood",
        "contrasts": {"ALS": (r"\bALS\b|amyotrophic", CONTROL)},
        # The replication set also contains ALS-mimic patients; exclude them.
        "exclude": r"mimic",
        "default": True,
    },
}


def default_cohorts() -> list[str]:
    return [k for k, v in COHORTS.items() if v.get("default")]
