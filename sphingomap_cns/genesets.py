"""Curated gene sets for sphingolipid / ceramide biology in neuroinflammation.

Two kinds of modules:

* **Sphingolipid modules** follow the canonical pathway (de novo synthesis,
  sphingomyelin cycle, ceramide catabolism, S1P axis, glycosphingolipid branch,
  ceramide transport). These are carried over from ``sphingomap``.
* **Context modules** capture the biology the pathway is coupled to in ALS,
  FTD and AD: cytokine triggers of sphingomyelinase activation, lipid
  peroxidation drivers and antioxidant defences, microglia / myeloid
  activation, regulatory T-cell (Treg) markers and axonal integrity genes.

Symbols are current HGNC symbols. ``ALIASES`` maps retired or alternative
symbols found in older microarray annotations back to the current name.
"""
from __future__ import annotations

SPHINGOLIPID = "sphingolipid"
CONTEXT = "context"

MODULES: dict[str, dict] = {
    # --- sphingolipid pathway -------------------------------------------------
    "de_novo_synthesis": {
        "label": "De novo synthesis", "kind": SPHINGOLIPID,
        "description": "Serine palmitoyltransferase -> 3-ketosphinganine -> dihydroceramide -> ceramide",
        "genes": ["SPTLC1", "SPTLC2", "SPTLC3", "KDSR", "CERS1", "CERS2",
                  "CERS3", "CERS4", "CERS5", "CERS6", "DEGS1", "DEGS2"],
    },
    "sphingomyelin_cycle": {
        "label": "Sphingomyelin cycle", "kind": SPHINGOLIPID,
        "description": "Sphingomyelin synthases and acid/neutral sphingomyelinases",
        "genes": ["SGMS1", "SGMS2", "SMPD1", "SMPD2", "SMPD3", "SMPD4"],
    },
    "ceramide_catabolism": {
        "label": "Ceramide catabolism", "kind": SPHINGOLIPID,
        "description": "Acid, neutral and alkaline ceramidases releasing sphingosine",
        "genes": ["ASAH1", "ASAH2", "ACER1", "ACER2", "ACER3"],
    },
    "s1p_axis": {
        "label": "S1P axis", "kind": SPHINGOLIPID,
        "description": "Sphingosine kinases, S1P phosphatases/lyase, S1P transporter and receptors",
        "genes": ["SPHK1", "SPHK2", "SGPP1", "SGPP2", "SGPL1", "SPNS2",
                  "S1PR1", "S1PR2", "S1PR3", "S1PR4", "S1PR5"],
    },
    "glycosphingolipid_branch": {
        "label": "Glycosphingolipid branch", "kind": SPHINGOLIPID,
        "description": "GlcCer/LacCer/ganglioside synthesis and lysosomal GSL degradation",
        "genes": ["UGCG", "B4GALT5", "B4GALT6", "ST3GAL5", "A4GALT",
                  "GBA1", "GBA2", "GLA", "GLB1", "HEXA", "HEXB"],
    },
    "transport": {
        "label": "Ceramide transport", "kind": SPHINGOLIPID,
        "description": "ER-to-Golgi ceramide transfer (CERT)",
        "genes": ["CERT1"],
    },
    # --- neuroinflammatory context -------------------------------------------
    "smase_triggers": {
        "label": "Cytokine SMase triggers", "kind": CONTEXT,
        "description": "TNF-alpha / IL-1beta / IFN-gamma and receptors; NSMAF couples TNFR1 to neutral SMase",
        "genes": ["TNF", "IL1B", "IFNG", "TNFRSF1A", "IL1R1", "IFNGR1", "NSMAF"],
    },
    "peroxidation_drivers": {
        "label": "Lipid peroxidation drivers", "kind": CONTEXT,
        "description": "PUFA-phospholipid loading, lipoxygenases, COX-2 and NOX2 (ROS)",
        "genes": ["ACSL4", "LPCAT3", "ALOX5", "ALOX12", "ALOX15", "ALOX15B", "PTGS2", "CYBB", "NCF1"],
    },
    "antioxidant_defense": {
        "label": "Antioxidant / 4-HNE defence", "kind": CONTEXT,
        "description": "GPX4-GSH and FSP1 systems, NRF2 targets, 4-HNE detoxification",
        "genes": ["GPX4", "SLC7A11", "AIFM2", "NFE2L2", "HMOX1", "ALDH2", "GSTA4", "AKR1C1"],
    },
    "microglia_myeloid": {
        "label": "Microglia / myeloid activation", "kind": CONTEXT,
        "description": "Activated microglia, monocytes and macrophages",
        "genes": ["AIF1", "CD68", "TREM2", "TYROBP", "ITGAM", "CD14", "C1QA"],
    },
    "treg_axis": {
        "label": "Treg axis", "kind": CONTEXT,
        "description": "Regulatory T-cell identity and suppressive markers (IL-2 / CTLA4 biology)",
        "genes": ["FOXP3", "IL2RA", "CTLA4", "IKZF2", "TNFRSF18", "IL2RB", "IL10", "TGFB1"],
    },
    "axonal_integrity": {
        "label": "Axonal integrity", "kind": CONTEXT,
        "description": "Neurofilament and intermediate-filament genes (tissue proxy for neuronal content; NfL = NEFL)",
        "genes": ["NEFL", "NEFM", "NEFH", "PRPH", "INA"],
    },
}

# Genes named in the Coya proposal as the headline Treg-modulated lipid genes.
FOCUS_GENES = ["SMPD1", "SMPD2", "SMPD3", "CERS1", "CERS2", "CERS3", "CERS4", "CERS5", "CERS6",
               "ASAH1", "SGMS1", "SGMS2", "UGCG", "SPHK1", "S1PR1", "GPX4", "ACSL4"]

ALIASES: dict[str, str] = {
    "LASS1": "CERS1", "LASS2": "CERS2", "LASS3": "CERS3",
    "LASS4": "CERS4", "LASS5": "CERS5", "LASS6": "CERS6",
    "GBA": "GBA1", "COL4A3BP": "CERT1", "SIAT9": "ST3GAL5",
    "EDG1": "S1PR1", "EDG5": "S1PR2", "EDG3": "S1PR3",
    "EDG6": "S1PR4", "EDG8": "S1PR5", "FVT1": "KDSR",
    "ASAHL": "ASAH2", "ASAH3": "ACER1", "ASAH3L": "ACER2", "PHCA": "ACER3",
    "FSP1": "AIFM2", "AMID": "AIFM2", "NRF2": "NFE2L2",
    "NEF3": "NEFM", "FACL4": "ACSL4", "ACS4": "ACSL4",
    "TNFA": "TNF", "TNFR1": "TNFRSF1A", "GITR": "TNFRSF18", "HELIOS": "IKZF2",
}

# Sphingolipid rheostat (Cuvillier et al., Nature 1996): pro-survival S1P/GSL
# minus pro-apoptotic ceramide generation. Transcript-level proxy only.
RHEOSTAT = {
    "pro_survival": ["SPHK1", "SPHK2", "S1PR1", "SPNS2", "UGCG", "B4GALT5", "B4GALT6", "ACER2"],
    "pro_ceramide": ["CERS2", "CERS5", "CERS6", "SMPD1", "SMPD3", "SGPP1", "SGPL1", "GBA1"],
}

# Ceramide-peroxidation axis (CPA) index: ceramide generation + peroxidation
# drivers minus ceramide clearance into SM/GlcCer + antioxidant defence.
# Exploratory transcript proxy for the Phase 2 lipid-measured risk score; it is
# NOT a measurement of ceramide, 4-HNE or MDA.
CPA_INDEX = {
    "up": ["SMPD1", "SMPD2", "SMPD3", "NSMAF", "CERS2", "CERS5", "CERS6",
           "ACSL4", "LPCAT3", "ALOX5", "ALOX15", "CYBB", "NCF1"],
    "down": ["SGMS1", "SGMS2", "UGCG", "GPX4", "SLC7A11", "AIFM2", "ALDH2", "GSTA4"],
}

COMPOSITE_INDICES = {"rheostat_index": (RHEOSTAT["pro_survival"], RHEOSTAT["pro_ceramide"]),
                     "cpa_index": (CPA_INDEX["up"], CPA_INDEX["down"])}

# Pathway diagram coordinates (x, y) for plots.pathway_map.
PATHWAY_LAYOUT: dict[str, tuple[float, float]] = {
    # de novo
    "SPTLC1": (0.0, 6.0), "SPTLC2": (1.0, 6.0), "KDSR": (2.0, 6.0),
    "CERS1": (3.0, 7.0), "CERS2": (3.0, 6.3), "CERS5": (3.0, 5.6),
    "CERS4": (4.0, 7.0), "CERS6": (4.0, 6.3), "DEGS1": (4.0, 5.6),
    # SM cycle
    "SGMS1": (1.6, 4.1), "SGMS2": (1.6, 3.5), "SMPD1": (3.0, 3.6), "SMPD2": (3.0, 3.0), "SMPD3": (3.0, 2.4),
    # catabolism / S1P
    "ASAH1": (5.3, 5.0), "ACER2": (5.3, 3.2),
    "SPHK1": (7.1, 5.0), "SPHK2": (7.1, 3.2),
    "SGPP1": (9.0, 5.2), "SGPL1": (9.0, 2.8), "S1PR1": (8.4, 1.9), "SPNS2": (7.2, 1.9),
    # GSL branch
    "UGCG": (5.0, 7.5), "GBA1": (6.0, 7.5), "B4GALT5": (7.0, 7.5), "B4GALT6": (8.0, 7.5), "ST3GAL5": (9.0, 7.5),
    # inflammatory trigger -> nSMase
    "TNF": (-0.2, 1.3), "IL1B": (0.7, 1.3), "IFNG": (1.6, 1.3), "NSMAF": (2.1, 2.2),
    # peroxidation
    "ACSL4": (3.9, 0.6), "ALOX15": (4.8, 0.6), "CYBB": (5.7, 0.6),
    "GPX4": (3.9, -0.05), "SLC7A11": (4.8, -0.05), "AIFM2": (5.7, -0.05),
}

PATHWAY_NODES: dict[str, tuple[float, float]] = {
    "Serine +\nPalmitoyl-CoA": (0.5, 7.2),
    "Ceramide": (4.5, 4.5),
    "Sphingomyelin": (0.6, 3.8),
    "Sphingosine": (6.2, 4.0),
    "S1P": (8.2, 4.0),
    "GlcCer -> LacCer\n-> GM3": (7.0, 8.4),
    "TNF-a / IL-1b / IFN-g": (0.7, 0.55),
    "ROS / lipid peroxidation\n(4-HNE, MDA)": (7.6, 0.3),
}


def all_genes(kind: str | None = None) -> list[str]:
    """Unique gene list across modules (optionally only one kind), in module order."""
    seen: list[str] = []
    for mod in MODULES.values():
        if kind and mod["kind"] != kind:
            continue
        for g in mod["genes"]:
            if g not in seen:
                seen.append(g)
    return seen


def gene_to_module() -> dict[str, str]:
    return {g: name for name, mod in MODULES.items() for g in mod["genes"]}
