# sphingomap-CNS report: GSE153960 ALS - Motor cortex (lateral)

_sphingomap-CNS v0.1.0, generated 2026-11-11_

Source: NYGC ALS Consortium / Target ALS post-mortem CNS RNA-seq (New York Genome Center ALS Consortium (GEO GSE153960))

## Design

- ALS: **83**, Control: **19**
- Model: linear model, adjusted for microglia_myeloid_score
- Genes tested: 78 (not in data / not expressed: CERS3, ACER1, S1PR4, TNF, IFNG, ALOX15, IL2RA, CTLA4, TNFRSF18, IL2RB, IL10, PRPH)

## Gene-level changes

22 genes with FDR < 0.05 and |log2FC| >= 0.25.

- Up: ACSL4, ASAH2, CERS6, UGCG, CERT1, B4GALT6, IKZF2, SPTLC2, ACER3, ASAH1, SGPP1, GSTA4, SPTLC1, B4GALT5, DEGS1, KDSR
- Down: SMPD3, CERS1, SPHK2, AIFM2, SPHK1, ALOX5

![pathway](figures/pathway_map.png)

![volcano](figures/volcano.png)

### Proposal focus genes

| Gene | log2FC | FDR |
|---|---:|---:|
| SMPD1 | -0.12 | 2.59e-01 |
| SMPD2 | -0.12 | 2.50e-01 |
| SMPD3 | -0.48 | 6.23e-03 |
| CERS1 | -0.37 | 1.83e-02 |
| CERS2 | +0.04 | 8.85e-01 |
| CERS4 | -0.16 | 1.72e-01 |
| CERS5 | +0.17 | 1.22e-01 |
| CERS6 | +0.71 | 4.65e-03 |
| ASAH1 | +0.40 | 2.97e-03 |
| SGMS1 | +0.18 | 7.92e-02 |
| SGMS2 | +0.27 | 1.08e-01 |
| UGCG | +0.65 | 2.15e-03 |
| SPHK1 | -0.27 | 2.84e-02 |
| S1PR1 | -0.09 | 5.52e-01 |
| GPX4 | -0.09 | 5.47e-01 |
| ACSL4 | +0.82 | 8.33e-04 |

### Top 25 genes

| Gene | Module | log2FC | FDR |
|---|---|---:|---:|
| ACSL4 | Lipid peroxidation drivers | +0.82 | 8.33e-04 |
| CERT1 | Ceramide transport | +0.60 | 8.33e-04 |
| ASAH2 | Ceramide catabolism | +0.72 | 1.28e-03 |
| UGCG | Glycosphingolipid branch | +0.65 | 2.15e-03 |
| ASAH1 | Ceramide catabolism | +0.40 | 2.97e-03 |
| SGPP1 | S1P axis | +0.35 | 2.97e-03 |
| ACER3 | Ceramide catabolism | +0.46 | 3.18e-03 |
| IKZF2 | Treg axis | +0.51 | 3.18e-03 |
| SPTLC2 | De novo synthesis | +0.49 | 4.36e-03 |
| CERS6 | De novo synthesis | +0.71 | 4.65e-03 |
| KDSR | De novo synthesis | +0.26 | 6.16e-03 |
| SPTLC1 | De novo synthesis | +0.31 | 6.16e-03 |
| SMPD3 | Sphingomyelin cycle | -0.48 | 6.23e-03 |
| SPHK2 | S1P axis | -0.33 | 1.29e-02 |
| AIFM2 | Antioxidant / 4-HNE defence | -0.32 | 1.77e-02 |
| CERS1 | De novo synthesis | -0.37 | 1.83e-02 |
| FOXP3 | Treg axis | -0.18 | 2.34e-02 |
| B4GALT6 | Glycosphingolipid branch | +0.59 | 2.34e-02 |
| DEGS1 | De novo synthesis | +0.27 | 2.34e-02 |
| ST3GAL5 | Glycosphingolipid branch | +0.22 | 2.34e-02 |
| SPHK1 | S1P axis | -0.27 | 2.84e-02 |
| B4GALT5 | Glycosphingolipid branch | +0.27 | 3.03e-02 |
| GSTA4 | Antioxidant / 4-HNE defence | +0.35 | 3.03e-02 |
| GLA | Glycosphingolipid branch | +0.19 | 3.03e-02 |
| NSMAF | Cytokine SMase triggers | +0.18 | 3.58e-02 |

## Module scores and indices

Scores are mean z-scores relative to the control group. The rheostat index is pro-survival (S1P/GSL) minus pro-ceramide genes; the ceramide-peroxidation (CPA) index is ceramide-generation + peroxidation-driver genes minus ceramide-clearance + antioxidant genes.

| Score | Mean difference | Hedges' g | FDR |
|---|---:|---:|---:|
| Ceramide catabolism | +0.72 | +1.47 | 2.42e-06 |
| De novo synthesis | +0.23 | +0.83 | 2.35e-02 |
| Ceramide-peroxidation index | -0.22 | -0.38 | 1.71e-01 |
| Glycosphingolipid branch | +0.19 | +0.43 | 3.80e-01 |
| Sphingomyelin cycle | -0.18 | -0.31 | 3.80e-01 |
| Cytokine SMase triggers | +0.15 | +0.46 | 3.80e-01 |
| S1P axis | -0.13 | -0.21 | 3.80e-01 |
| Microglia / myeloid activation | +0.00 | +0.32 | 7.30e-01 |
| Antioxidant / 4-HNE defence | +0.05 | +0.29 | 7.73e-01 |
| Rheostat index | -0.05 | -0.17 | 8.30e-01 |
| Lipid peroxidation drivers | -0.02 | +0.20 | 9.06e-01 |
| Treg axis | +0.03 | +0.20 | 9.06e-01 |
| Axonal integrity | +0.03 | +0.00 | 9.06e-01 |

![scores](figures/module_scores.png)

![correlation](figures/score_correlation.png)

![heatmap](figures/heatmap.png)

## Caveats

- mRNA / protein abundance is not enzyme activity or lipid concentration; confirm with lipidomics (LC-MS/MS, HPTLC).
- Module scores and indices are exploratory transcript-level heuristics, not validated biomarkers.
- Post-mortem bulk tissue mixes cell types; changes can reflect cell-composition shifts (e.g. neuron loss, gliosis) rather than per-cell regulation.
