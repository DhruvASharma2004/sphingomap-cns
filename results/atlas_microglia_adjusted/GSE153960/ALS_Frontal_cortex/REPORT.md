# sphingomap-CNS report: GSE153960 ALS - Frontal cortex

_sphingomap-CNS v0.1.0, generated 2026-11-11_

Source: NYGC ALS Consortium / Target ALS post-mortem CNS RNA-seq (New York Genome Center ALS Consortium (GEO GSE153960))

## Design

- ALS: **156**, Control: **56**
- Model: linear model, adjusted for microglia_myeloid_score
- Genes tested: 78 (not in data / not expressed: CERS3, ACER1, S1PR4, TNF, IFNG, ALOX15, IL2RA, CTLA4, TNFRSF18, IL2RB, IL10, PRPH)

## Gene-level changes

30 genes with FDR < 0.05 and |log2FC| >= 0.25.

- Up: ACSL4, UGCG, CERT1, CERS6, INA, B4GALT6, ASAH2, SPTLC2, ACER3, NEFL, ASAH1, SGPP1, DEGS1, GSTA4, NEFM, SPTLC1, CYBB, KDSR
- Down: ALOX12, A4GALT, AIFM2, CERS1, SMPD3, SMPD4, TGFB1, SPHK2, DEGS2, ALOX5, SPNS2, CERS4

![pathway](figures/pathway_map.png)

![volcano](figures/volcano.png)

### Proposal focus genes

| Gene | log2FC | FDR |
|---|---:|---:|
| SMPD1 | -0.05 | 3.22e-01 |
| SMPD2 | -0.20 | 1.82e-04 |
| SMPD3 | -0.36 | 2.60e-05 |
| CERS1 | -0.43 | 1.41e-08 |
| CERS2 | +0.05 | 5.39e-01 |
| CERS4 | -0.27 | 5.73e-06 |
| CERS5 | -0.20 | 4.01e-04 |
| CERS6 | +0.53 | 1.01e-06 |
| ASAH1 | +0.37 | 1.41e-08 |
| SGMS1 | +0.12 | 5.60e-03 |
| SGMS2 | +0.15 | 6.22e-02 |
| UGCG | +0.53 | 1.74e-07 |
| SPHK1 | -0.16 | 3.79e-02 |
| S1PR1 | -0.13 | 9.95e-02 |
| GPX4 | +0.12 | 7.33e-02 |
| ACSL4 | +0.70 | 1.41e-08 |

### Top 25 genes

| Gene | Module | log2FC | FDR |
|---|---|---:|---:|
| CERT1 | Ceramide transport | +0.53 | 1.38e-08 |
| ACSL4 | Lipid peroxidation drivers | +0.70 | 1.41e-08 |
| AIFM2 | Antioxidant / 4-HNE defence | -0.43 | 1.41e-08 |
| CERS1 | De novo synthesis | -0.43 | 1.41e-08 |
| ASAH1 | Ceramide catabolism | +0.37 | 1.41e-08 |
| FOXP3 | Treg axis | -0.23 | 1.41e-08 |
| ALOX12 | Lipid peroxidation drivers | -0.57 | 4.07e-08 |
| UGCG | Glycosphingolipid branch | +0.53 | 1.74e-07 |
| SMPD4 | Sphingomyelin cycle | -0.35 | 1.74e-07 |
| SGPP1 | S1P axis | +0.37 | 2.45e-07 |
| ACER3 | Ceramide catabolism | +0.39 | 2.45e-07 |
| ASAH2 | Ceramide catabolism | +0.49 | 2.45e-07 |
| DEGS2 | De novo synthesis | -0.29 | 3.30e-07 |
| SPTLC2 | De novo synthesis | +0.40 | 3.33e-07 |
| KDSR | De novo synthesis | +0.25 | 5.07e-07 |
| HEXA | Glycosphingolipid branch | -0.23 | 6.14e-07 |
| SPHK2 | S1P axis | -0.31 | 7.90e-07 |
| CERS6 | De novo synthesis | +0.53 | 1.01e-06 |
| LPCAT3 | Lipid peroxidation drivers | -0.21 | 1.01e-06 |
| DEGS1 | De novo synthesis | +0.30 | 1.70e-06 |
| B4GALT6 | Glycosphingolipid branch | +0.50 | 4.10e-06 |
| A4GALT | Glycosphingolipid branch | -0.50 | 4.83e-06 |
| ST3GAL5 | Glycosphingolipid branch | +0.19 | 5.04e-06 |
| CERS4 | De novo synthesis | -0.27 | 5.73e-06 |
| GSTA4 | Antioxidant / 4-HNE defence | +0.30 | 6.63e-06 |

## Module scores and indices

Scores are mean z-scores relative to the control group. The rheostat index is pro-survival (S1P/GSL) minus pro-ceramide genes; the ceramide-peroxidation (CPA) index is ceramide-generation + peroxidation-driver genes minus ceramide-clearance + antioxidant genes.

| Score | Mean difference | Hedges' g | FDR |
|---|---:|---:|---:|
| Ceramide catabolism | +0.49 | +0.82 | 1.08e-05 |
| Lipid peroxidation drivers | -0.24 | -0.34 | 1.29e-05 |
| Ceramide-peroxidation index | -0.34 | -0.62 | 1.85e-05 |
| Treg axis | -0.37 | -0.50 | 8.26e-05 |
| S1P axis | -0.21 | -0.37 | 1.72e-03 |
| Sphingomyelin cycle | -0.32 | -0.49 | 1.80e-03 |
| Axonal integrity | +0.38 | +0.43 | 7.50e-03 |
| Glycosphingolipid branch | +0.10 | +0.26 | 3.40e-01 |
| Microglia / myeloid activation | +0.00 | +0.24 | 7.46e-01 |
| Rheostat index | -0.02 | -0.08 | 8.33e-01 |
| Cytokine SMase triggers | -0.03 | +0.11 | 8.33e-01 |
| De novo synthesis | +0.01 | +0.12 | 9.47e-01 |
| Antioxidant / 4-HNE defence | -0.00 | +0.12 | 9.47e-01 |

![scores](figures/module_scores.png)

![correlation](figures/score_correlation.png)

![heatmap](figures/heatmap.png)

## Caveats

- mRNA / protein abundance is not enzyme activity or lipid concentration; confirm with lipidomics (LC-MS/MS, HPTLC).
- Module scores and indices are exploratory transcript-level heuristics, not validated biomarkers.
- Post-mortem bulk tissue mixes cell types; changes can reflect cell-composition shifts (e.g. neuron loss, gliosis) rather than per-cell regulation.
