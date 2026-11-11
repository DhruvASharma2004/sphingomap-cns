# sphingomap-CNS report: GSE112676 ALS

_sphingomap-CNS v0.1.0, generated 2026-11-11_

Source: ALS whole blood, discovery set (Illumina HT-12 v3) (van Rheenen W. et al., PLoS One 13, e0198874 (2018))

## Design

- ALS: **233**, Control: **508**
- Model: linear model, adjusted for sex_male
- Genes tested: 66 (not in data / not expressed: CERS1, CERS3, CERS4, DEGS2, ACER1, ACER2, SGPP1, SPNS2, S1PR2, B4GALT6, A4GALT, GLA, IFNG, ACSL4, CYBB, NCF1, SLC7A11, GSTA4, AKR1C1, TREM2, FOXP3, IL10, TGFB1, INA)

## Gene-level changes

12 genes with FDR < 0.05 and |log2FC| >= 0.25.

- Up: IFNGR1, DEGS1, PTGS2, NFE2L2, ITGAM, NSMAF, HEXB
- Down: IL2RB, SPTLC1, CD68, S1PR5, SPHK2

![pathway](figures/pathway_map.png)

![volcano](figures/volcano.png)

### Proposal focus genes

| Gene | log2FC | FDR |
|---|---:|---:|
| SMPD1 | -0.08 | 6.96e-06 |
| SMPD2 | +0.02 | 4.11e-01 |
| SMPD3 | -0.09 | 1.71e-05 |
| CERS2 | +0.02 | 6.29e-01 |
| CERS5 | +0.05 | 2.22e-01 |
| CERS6 | +0.11 | 1.02e-02 |
| ASAH1 | +0.00 | 9.44e-01 |
| SGMS1 | +0.04 | 5.35e-05 |
| SGMS2 | +0.00 | 9.65e-01 |
| UGCG | +0.11 | 1.68e-03 |
| SPHK1 | -0.05 | 1.54e-02 |
| S1PR1 | +0.18 | 2.70e-05 |
| GPX4 | +0.18 | 4.21e-06 |

### Top 25 genes

| Gene | Module | log2FC | FDR |
|---|---|---:|---:|
| PTGS2 | Lipid peroxidation drivers | +0.45 | 3.11e-26 |
| IFNGR1 | Cytokine SMase triggers | +0.61 | 1.54e-25 |
| DEGS1 | De novo synthesis | +0.50 | 2.93e-18 |
| NSMAF | Cytokine SMase triggers | +0.31 | 1.85e-17 |
| IL2RB | Treg axis | -0.42 | 1.07e-16 |
| NFE2L2 | Antioxidant / 4-HNE defence | +0.41 | 1.86e-16 |
| HEXB | Glycosphingolipid branch | +0.29 | 1.58e-15 |
| SPHK2 | S1P axis | -0.32 | 2.37e-15 |
| CD68 | Microglia / myeloid activation | -0.35 | 8.23e-15 |
| SPTLC1 | De novo synthesis | -0.38 | 1.49e-14 |
| S1PR5 | S1P axis | -0.34 | 3.75e-13 |
| GBA2 | Glycosphingolipid branch | -0.19 | 1.08e-10 |
| B4GALT5 | Glycosphingolipid branch | +0.24 | 1.13e-09 |
| CERT1 | Ceramide transport | +0.22 | 1.31e-09 |
| ITGAM | Microglia / myeloid activation | +0.36 | 8.59e-09 |
| S1PR3 | S1P axis | +0.09 | 2.28e-08 |
| S1PR4 | S1P axis | +0.25 | 2.28e-08 |
| TYROBP | Microglia / myeloid activation | +0.14 | 8.11e-08 |
| SMPD4 | Sphingomyelin cycle | -0.18 | 3.17e-06 |
| GPX4 | Antioxidant / 4-HNE defence | +0.18 | 4.21e-06 |
| SMPD1 | Sphingomyelin cycle | -0.08 | 6.96e-06 |
| SMPD3 | Sphingomyelin cycle | -0.09 | 1.71e-05 |
| S1PR1 | S1P axis | +0.18 | 2.70e-05 |
| SGMS1 | Sphingomyelin cycle | +0.04 | 5.35e-05 |
| ALOX15B | Lipid peroxidation drivers | -0.09 | 1.94e-04 |

## Module scores and indices

Scores are mean z-scores relative to the control group. The rheostat index is pro-survival (S1P/GSL) minus pro-ceramide genes; the ceramide-peroxidation (CPA) index is ceramide-generation + peroxidation-driver genes minus ceramide-clearance + antioxidant genes.

| Score | Mean difference | Hedges' g | FDR |
|---|---:|---:|---:|
| Cytokine SMase triggers | +0.38 | +0.76 | 1.56e-19 |
| Treg axis | -0.22 | -0.52 | 3.96e-10 |
| Antioxidant / 4-HNE defence | +0.18 | +0.37 | 1.33e-05 |
| Glycosphingolipid branch | +0.13 | +0.31 | 3.98e-04 |
| Sphingomyelin cycle | -0.11 | -0.28 | 9.55e-04 |
| Lipid peroxidation drivers | +0.12 | +0.28 | 1.12e-03 |
| Rheostat index | +0.11 | +0.26 | 1.62e-03 |
| Ceramide-peroxidation index | -0.10 | -0.22 | 1.00e-02 |
| Axonal integrity | -0.03 | -0.07 | 5.11e-01 |
| S1P axis | -0.02 | -0.05 | 6.79e-01 |
| Microglia / myeloid activation | -0.02 | -0.04 | 6.95e-01 |
| De novo synthesis | +0.01 | +0.03 | 6.95e-01 |
| Ceramide catabolism | -0.01 | -0.03 | 6.95e-01 |

![scores](figures/module_scores.png)

![correlation](figures/score_correlation.png)

![heatmap](figures/heatmap.png)

## Caveats

- mRNA / protein abundance is not enzyme activity or lipid concentration; confirm with lipidomics (LC-MS/MS, HPTLC).
- Module scores and indices are exploratory transcript-level heuristics, not validated biomarkers.
- Post-mortem bulk tissue mixes cell types; changes can reflect cell-composition shifts (e.g. neuron loss, gliosis) rather than per-cell regulation.
