# sphingomap-CNS report: GSE112680 ALS

_sphingomap-CNS v0.1.0, generated 2026-11-11_

Source: ALS whole blood, replication set (Illumina HT-12 v4) (van Rheenen W. et al., PLoS One 13, e0198874 (2018))

## Design

- ALS: **164**, Control: **137**
- Model: linear model, adjusted for microglia_myeloid_score
- Genes tested: 67 (not in data / not expressed: CERS1, CERS3, CERS4, DEGS2, ACER1, SGPP1, SPNS2, S1PR2, B4GALT6, A4GALT, GLA, HEXA, IFNG, IL1R1, ACSL4, CYBB, NCF1, SLC7A11, AIFM2, AKR1C1, FOXP3, IL10, INA)

## Gene-level changes

3 genes with FDR < 0.05 and |log2FC| >= 0.25.

- Up: IFNGR1
- Down: IL2RB, SPTLC1

![pathway](figures/pathway_map.png)

![volcano](figures/volcano.png)

### Proposal focus genes

| Gene | log2FC | FDR |
|---|---:|---:|
| SMPD1 | +0.04 | 1.87e-01 |
| SMPD2 | +0.05 | 2.13e-01 |
| SMPD3 | -0.03 | 2.60e-02 |
| CERS2 | -0.06 | 1.77e-02 |
| CERS5 | +0.04 | 1.71e-01 |
| CERS6 | +0.00 | 9.18e-01 |
| ASAH1 | +0.01 | 5.26e-01 |
| SGMS1 | -0.01 | 2.92e-01 |
| SGMS2 | +0.01 | 3.90e-01 |
| UGCG | -0.05 | 1.11e-01 |
| SPHK1 | +0.04 | 9.38e-02 |
| S1PR1 | -0.19 | 1.31e-09 |
| GPX4 | +0.11 | 4.27e-03 |

### Top 25 genes

| Gene | Module | log2FC | FDR |
|---|---|---:|---:|
| S1PR1 | S1P axis | -0.19 | 1.31e-09 |
| IL2RB | Treg axis | -0.33 | 1.85e-08 |
| GLB1 | Glycosphingolipid branch | -0.16 | 1.85e-08 |
| IFNGR1 | Cytokine SMase triggers | +0.34 | 5.83e-07 |
| TNFRSF1A | Cytokine SMase triggers | +0.20 | 6.00e-07 |
| S1PR4 | S1P axis | +0.24 | 7.85e-07 |
| TYROBP | Microglia / myeloid activation | +0.12 | 7.85e-07 |
| CD68 | Microglia / myeloid activation | -0.23 | 1.70e-05 |
| HMOX1 | Antioxidant / 4-HNE defence | -0.13 | 3.53e-05 |
| ST3GAL5 | Glycosphingolipid branch | -0.09 | 6.92e-05 |
| S1PR5 | S1P axis | -0.21 | 6.92e-05 |
| GBA2 | Glycosphingolipid branch | +0.08 | 5.34e-04 |
| S1PR3 | S1P axis | +0.06 | 6.80e-04 |
| GBA1 | Glycosphingolipid branch | +0.10 | 1.67e-03 |
| SPTLC1 | De novo synthesis | -0.26 | 2.02e-03 |
| IL2RA | Treg axis | -0.05 | 2.26e-03 |
| TNFRSF18 | Treg axis | +0.05 | 3.81e-03 |
| GPX4 | Antioxidant / 4-HNE defence | +0.11 | 4.27e-03 |
| HEXB | Glycosphingolipid branch | +0.09 | 6.46e-03 |
| CERS2 | De novo synthesis | -0.06 | 1.77e-02 |
| SPTLC2 | De novo synthesis | +0.04 | 2.04e-02 |
| SMPD3 | Sphingomyelin cycle | -0.03 | 2.60e-02 |
| NFE2L2 | Antioxidant / 4-HNE defence | -0.10 | 3.50e-02 |
| GSTA4 | Antioxidant / 4-HNE defence | -0.02 | 3.73e-02 |
| PTGS2 | Lipid peroxidation drivers | +0.12 | 4.36e-02 |

## Module scores and indices

Scores are mean z-scores relative to the control group. The rheostat index is pro-survival (S1P/GSL) minus pro-ceramide genes; the ceramide-peroxidation (CPA) index is ceramide-generation + peroxidation-driver genes minus ceramide-clearance + antioxidant genes.

| Score | Mean difference | Hedges' g | FDR |
|---|---:|---:|---:|
| Microglia / myeloid activation | -0.00 | -0.86 | 1.65e-11 |
| Cytokine SMase triggers | +0.29 | +0.50 | 1.19e-04 |
| Rheostat index | -0.20 | -0.40 | 2.82e-03 |
| Antioxidant / 4-HNE defence | -0.16 | -0.36 | 6.93e-03 |
| Treg axis | -0.10 | -0.26 | 6.63e-02 |
| De novo synthesis | -0.08 | -0.24 | 8.78e-02 |
| Ceramide catabolism | -0.11 | -0.20 | 1.45e-01 |
| Lipid peroxidation drivers | -0.06 | -0.16 | 2.60e-01 |
| Sphingomyelin cycle | +0.03 | +0.06 | 7.91e-01 |
| Axonal integrity | -0.03 | -0.06 | 7.91e-01 |
| S1P axis | -0.01 | -0.02 | 9.53e-01 |
| Glycosphingolipid branch | +0.00 | +0.01 | 9.53e-01 |
| Ceramide-peroxidation index | +0.00 | +0.01 | 9.53e-01 |

![scores](figures/module_scores.png)

![correlation](figures/score_correlation.png)

![heatmap](figures/heatmap.png)

## Caveats

- mRNA / protein abundance is not enzyme activity or lipid concentration; confirm with lipidomics (LC-MS/MS, HPTLC).
- Module scores and indices are exploratory transcript-level heuristics, not validated biomarkers.
- Post-mortem bulk tissue mixes cell types; changes can reflect cell-composition shifts (e.g. neuron loss, gliosis) rather than per-cell regulation.
