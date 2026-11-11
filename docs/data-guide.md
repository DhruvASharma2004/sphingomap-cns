# Preparing your own data for sphingomap-CNS

This guide covers trial or partner datasets: bulk RNA-seq, targeted or untargeted proteomics (Olink, SomaScan,
mass spec) and single-cell proteomics (CyTOF, spectral flow).

## 1. Expression table

Features in rows, samples in columns. The first column is the **HGNC gene symbol** (for proteins, the symbol of the
target protein: `SMPD1`, `FOXP3`, `NEFL`...). TSV or CSV, gzip allowed.

| gene | P001_Baseline | P001_Week24 | P002_Baseline | ... |
|---|---|---|---|---|
| SMPD1 | 7.81 | 7.42 | 8.03 | |
| FOXP3 | 5.10 | 5.94 | 4.88 | |

- Raw RNA-seq counts: add `--counts` (converted to log2 CPM; library size uses all rows, so include every gene).
- Linear intensities (e.g. NPX already log2 → fine; raw MS intensities → auto log2).
- Features measured in < 50% of samples are dropped. Panels that miss some pathway genes are fine; modules need ≥ 2 genes.

## 2. Sample sheet

One row per column of the expression table.

| sample | subject | arm | timepoint | cell_type | age | sex | HNE_4 | MDA | NfL | ALSFRS_R |
|---|---|---|---|---|---|---|---|---|---|---|
| P001_Baseline | P001 | Active | Baseline | | 61 | M | 3.2 | 2.1 | 54 | 38 |

| Option | Column used for |
|---|---|
| `--group-col` + `--case` / `--control` | the comparison (e.g. `timepoint`, Week24 vs Baseline) |
| `--pair-col` | subject ID → paired, within-subject test |
| `--subset arm=Active` | restrict to one arm (repeatable) |
| `--stratum-col` | run separately per tissue / cell type |
| `--covariates` | adjust unpaired comparisons (numeric, or two-level categorical) |
| `--biomarkers` | numeric columns correlated (Spearman) with every module score |

## 3. Typical analyses for a Treg-expansion trial

```bash
# Treated arm, on-treatment vs baseline
sphingomap-cns run -e expr.tsv -s samples.csv --group-col timepoint --case Week24 --control Baseline \
  --pair-col subject --subset arm=Active --biomarkers HNE_4 MDA NfL ALSFRS_R -o results/active

# Same for placebo (the contrast that tells you whether the active-arm change is treatment-related)
sphingomap-cns run ... --subset arm=Placebo -o results/placebo

# Baseline stratification: high vs low CPA index responders (add a column, then compare)
sphingomap-cns run -e expr.tsv -s samples.csv --group-col responder --case Yes --control No \
  --subset timepoint=Baseline --covariates age sex -o results/responders
```

Arm-by-time interaction is not modelled directly. Compare the paired results for the two arms, or compute per-subject
change scores (`sample_scores.csv`) and test them between arms.

## 4. Data handling

Nothing leaves your machine: the pipeline reads local files and writes local results. Keep sponsor data
out of the git repository (the `data/` and `results/run/` folders are git-ignored).
