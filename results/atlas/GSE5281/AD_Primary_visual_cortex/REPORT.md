# sphingomap-CNS report: GSE5281 AD - Primary visual cortex

_sphingomap-CNS v0.1.0, generated 2026-11-11_

Source: Alzheimer's disease, six brain regions, laser-captured neurons (Affymetrix U133 Plus 2) (Liang W. S. et al., Physiol Genomics 28, 311 (2007))

## Design

- AD: **19**, Control: **12**
- Model: linear model, adjusted for sex_male, age
- Genes tested: 72 (not in data / not expressed: CERS1, CERS4, DEGS2, SMPD4, ASAH2, ACER1, GBA1, GLB1, TNF, IFNG, ALOX15, NCF1, AIF1, CD68, TREM2, IL2RA, IL10, PRPH)

## Gene-level changes

0 genes with FDR < 0.05 and |log2FC| >= 0.25.

- Up: -
- Down: -

![pathway](figures/pathway_map.png)

![volcano](figures/volcano.png)

### Proposal focus genes

| Gene | log2FC | FDR |
|---|---:|---:|
| SMPD1 | +0.21 | 6.33e-01 |
| SMPD2 | +0.81 | 1.67e-01 |
| SMPD3 | -0.32 | 4.68e-01 |
| CERS2 | +0.56 | 1.67e-01 |
| CERS3 | +0.63 | 3.08e-01 |
| CERS5 | -0.03 | 9.34e-01 |
| CERS6 | -0.64 | 2.38e-01 |
| ASAH1 | -0.13 | 4.67e-01 |
| SGMS1 | +0.09 | 7.24e-01 |
| SGMS2 | -0.79 | 3.16e-01 |
| UGCG | -0.64 | 2.25e-01 |
| SPHK1 | +0.34 | 4.86e-01 |
| S1PR1 | +0.32 | 4.97e-01 |
| GPX4 | -0.58 | 1.67e-01 |
| ACSL4 | -0.51 | 3.47e-01 |

### Top 25 genes

| Gene | Module | log2FC | FDR |
|---|---|---:|---:|
| GPX4 | Antioxidant / 4-HNE defence | -0.58 | 1.67e-01 |
| S1PR2 | S1P axis | +1.28 | 1.67e-01 |
| A4GALT | Glycosphingolipid branch | +1.36 | 1.67e-01 |
| SGPP2 | S1P axis | -0.68 | 1.67e-01 |
| SPTLC1 | De novo synthesis | -0.49 | 1.67e-01 |
| INA | Axonal integrity | -1.38 | 1.67e-01 |
| HEXB | Glycosphingolipid branch | -0.52 | 1.67e-01 |
| ACER2 | Ceramide catabolism | +0.48 | 1.67e-01 |
| CERT1 | Ceramide transport | -0.52 | 1.67e-01 |
| ST3GAL5 | Glycosphingolipid branch | -0.42 | 1.67e-01 |
| NEFL | Axonal integrity | -1.30 | 1.67e-01 |
| ALOX15B | Lipid peroxidation drivers | +0.90 | 1.67e-01 |
| CERS2 | De novo synthesis | +0.56 | 1.67e-01 |
| IKZF2 | Treg axis | +0.64 | 1.67e-01 |
| SMPD2 | Sphingomyelin cycle | +0.81 | 1.67e-01 |
| ALOX12 | Lipid peroxidation drivers | +0.81 | 1.67e-01 |
| PTGS2 | Lipid peroxidation drivers | -0.65 | 1.67e-01 |
| GSTA4 | Antioxidant / 4-HNE defence | -0.57 | 2.12e-01 |
| CYBB | Lipid peroxidation drivers | +0.70 | 2.22e-01 |
| UGCG | Glycosphingolipid branch | -0.64 | 2.25e-01 |
| B4GALT6 | Glycosphingolipid branch | -0.79 | 2.25e-01 |
| IL1B | Cytokine SMase triggers | -0.83 | 2.38e-01 |
| CERS6 | De novo synthesis | -0.64 | 2.38e-01 |
| SGPL1 | S1P axis | +0.33 | 2.38e-01 |
| GLA | Glycosphingolipid branch | -0.42 | 2.38e-01 |

## Module scores and indices

Scores are mean z-scores relative to the control group. The rheostat index is pro-survival (S1P/GSL) minus pro-ceramide genes; the ceramide-peroxidation (CPA) index is ceramide-generation + peroxidation-driver genes minus ceramide-clearance + antioxidant genes.

| Score | Mean difference | Hedges' g | FDR |
|---|---:|---:|---:|
| De novo synthesis | +0.32 | +0.92 | 2.49e-01 |
| Axonal integrity | -1.23 | -0.70 | 2.49e-01 |
| Glycosphingolipid branch | -0.52 | -0.66 | 2.49e-01 |
| S1P axis | +0.21 | +0.52 | 2.49e-01 |
| Lipid peroxidation drivers | +0.29 | +0.49 | 2.49e-01 |
| Microglia / myeloid activation | +0.31 | +0.52 | 2.49e-01 |
| Treg axis | +0.42 | +0.60 | 2.49e-01 |
| Ceramide-peroxidation index | +0.26 | +0.50 | 3.89e-01 |
| Ceramide catabolism | +0.22 | +0.40 | 5.14e-01 |
| Cytokine SMase triggers | -0.20 | -0.24 | 6.36e-01 |
| Antioxidant / 4-HNE defence | +0.11 | +0.24 | 6.57e-01 |
| Rheostat index | -0.08 | -0.23 | 6.57e-01 |
| Sphingomyelin cycle | -0.02 | -0.08 | 9.06e-01 |

![scores](figures/module_scores.png)

![correlation](figures/score_correlation.png)

![heatmap](figures/heatmap.png)

## Caveats

- mRNA / protein abundance is not enzyme activity or lipid concentration; confirm with lipidomics (LC-MS/MS, HPTLC).
- Module scores and indices are exploratory transcript-level heuristics, not validated biomarkers.
- Post-mortem bulk tissue mixes cell types; changes can reflect cell-composition shifts (e.g. neuron loss, gliosis) rather than per-cell regulation.
