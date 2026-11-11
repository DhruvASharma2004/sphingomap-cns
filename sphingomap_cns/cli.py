"""Command-line interface for sphingomap-CNS."""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__

EPILOG = """examples:
  sphingomap-cns demo                              synthetic atlas + longitudinal trial demo (offline)
  sphingomap-cns cohorts                           list registered public GEO cohorts
  sphingomap-cns inspect GSE153960                 show a cohort's sample annotations and group assignment
  sphingomap-cns atlas                             fetch + analyse all default cohorts, build the atlas
  sphingomap-cns atlas GSE5281 GSE112676           selected cohorts only
  sphingomap-cns run -e prot.tsv -s samples.csv --case Week24 --control Baseline \\
      --group-col timepoint --pair-col subject --subset arm=Active --biomarkers HNE_4 MDA NfL
  sphingomap-cns pseudobulk cells.csv -o data/pb --cell-type-col cell_type --metadata samples.csv
"""


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="sphingomap-cns", epilog=EPILOG,
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                description="Sphingolipid / ceramide / lipid-peroxidation pathway atlas for "
                                            "neurodegeneration transcriptomes and proteomics")
    p.add_argument("--version", action="version", version=f"sphingomap-cns {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("genes", help="print the curated gene sets and indices as JSON")
    sub.add_parser("cohorts", help="list the registered public GEO cohorts")

    i = sub.add_parser("inspect", help="download a cohort's annotations and show how samples are grouped")
    i.add_argument("cohort")
    i.add_argument("--datadir", default="data/raw")

    a = sub.add_parser("atlas", help="fetch + analyse public cohorts and build the cross-cohort atlas")
    a.add_argument("cohorts", nargs="*", help="GEO accessions (default: all default cohorts)")
    a.add_argument("--datadir", default="data/raw")
    a.add_argument("-o", "--outdir", default="results/atlas")
    a.add_argument("--adjust", nargs="*", default=[], metavar="SCORE",
                   help="module scores to use as covariates, e.g. microglia_myeloid (cell-composition adjustment)")

    r = sub.add_parser("run", help="analyse your own expression / proteomics table with a sample sheet")
    r.add_argument("-e", "--expression", required=True, help="features x samples table (first column = gene symbol)")
    r.add_argument("-s", "--samples", required=True, help="sample sheet CSV/TSV with a 'sample' column")
    r.add_argument("--case", required=True, help="value of the group column treated as case")
    r.add_argument("--control", required=True, help="value of the group column treated as control/reference")
    r.add_argument("--group-col", default="group")
    r.add_argument("--pair-col", help="subject ID column -> paired (within-subject) analysis")
    r.add_argument("--stratum-col", help="run separately per value (tissue, cell type...)")
    r.add_argument("--subset", nargs="*", default=[], help="keep rows where COL=VALUE (repeatable)")
    r.add_argument("--biomarkers", nargs="*", default=[], help="numeric columns to correlate with scores")
    r.add_argument("--covariates", nargs="*", default=[], help="columns to adjust for (unpaired design)")
    r.add_argument("--counts", action="store_true", help="values are raw RNA-seq counts (-> log2 CPM)")
    r.add_argument("-l", "--label", default="dataset")
    r.add_argument("-o", "--outdir", default="results/run")

    b = sub.add_parser("pseudobulk", help="aggregate a cells x markers table to per-sample (x cell type) means")
    b.add_argument("cells")
    b.add_argument("-o", "--out", default="data/pseudobulk")
    b.add_argument("--sample-col", default="sample")
    b.add_argument("--cell-type-col")
    b.add_argument("--min-cells", type=int, default=20)
    b.add_argument("--median", action="store_true")
    b.add_argument("--metadata", help="per-sample sheet to join (must have a 'sample' column)")

    d = sub.add_parser("demo", help="offline demo: synthetic multi-cohort atlas + longitudinal trial")
    d.add_argument("-o", "--outdir", default="results/demo")
    args = p.parse_args(argv)

    if args.cmd == "genes":
        from .genesets import COMPOSITE_INDICES, MODULES
        print(json.dumps({"modules": MODULES, "indices": COMPOSITE_INDICES}, indent=2))
    elif args.cmd == "cohorts":
        from .registry import COHORTS
        for k, v in COHORTS.items():
            flag = "default" if v.get("default") else "optional"
            print(f"{k:<11} [{flag:<8}] {v['compartment']:<5} {v['platform']:<6} {v['title']}")
            print(f"{'':<11} contrasts: {', '.join(v['contrasts'])}; strata: "
                  f"{', '.join(v.get('strata') or ['all samples'])}")
            if v.get("note"):
                print(f"{'':<11} note: {v['note']}")
    elif args.cmd == "inspect":
        _inspect(args.cohort, args.datadir)
    elif args.cmd == "atlas":
        from .atlas import build_atlas
        from .registry import default_cohorts
        build_atlas(args.cohorts or default_cohorts(), args.datadir, args.outdir, adjust=args.adjust)
        print(f"Atlas written to {args.outdir}/ATLAS_REPORT.md and {args.outdir}/atlas.html")
    elif args.cmd == "run":
        from .userdata import run_user
        run_user(args.expression, args.samples, args.outdir, args.case, args.control, args.group_col,
                 args.pair_col, args.stratum_col, args.subset, args.biomarkers, args.covariates,
                 args.counts, args.label)
    elif args.cmd == "pseudobulk":
        from .userdata import pseudobulk
        pseudobulk(args.cells, args.out, args.sample_col, args.cell_type_col, args.min_cells,
                   "median" if args.median else "mean", args.metadata)
    elif args.cmd == "demo":
        demo(args.outdir)
    return 0


def demo(outdir: str) -> None:
    from pathlib import Path

    from .atlas import build_atlas
    from .simulate import simulate_geo_cohorts, simulate_trial
    from .userdata import run_user
    prepared, registry = simulate_geo_cohorts()
    build_atlas(list(prepared), None, f"{outdir}/atlas", prepared=prepared, registry=registry)
    paths = simulate_trial(Path(outdir) / "trial_data")
    run_user(paths["expression"], paths["samples"], f"{outdir}/trial_active", "Week24", "Baseline",
             group_col="timepoint", pair_col="subject", subset=["arm=Active"],
             biomarkers=["HNE_4_ng_ml", "MDA_uM", "NfL_pg_ml"], label="Synthetic trial, active arm")
    run_user(paths["expression"], paths["samples"], f"{outdir}/trial_placebo", "Week24", "Baseline",
             group_col="timepoint", pair_col="subject", subset=["arm=Placebo"],
             biomarkers=["HNE_4_ng_ml", "MDA_uM", "NfL_pg_ml"], label="Synthetic trial, placebo arm")
    print(f"Demo done (SYNTHETIC DATA): {outdir}/atlas/atlas.html, {outdir}/trial_active/REPORT.md")


def _inspect(cid: str, datadir: str) -> None:
    from . import geo
    from .design import assign_groups, assign_strata
    from .registry import COHORTS
    cfg = COHORTS.get(cid)
    paths = [geo.download(u, f"{datadir}/{cid}/{u.rsplit('/', 1)[1]}") for u in geo.series_matrix_urls(cid)]
    ann, _ = geo.load_series(paths)
    print(f"{cid}: {len(ann)} samples\n")
    for col in ann.columns:
        vc = ann[col].value_counts()
        if len(vc) > 25:
            print(f"- {col}: {len(vc)} distinct values (e.g. {', '.join(map(str, vc.index[:3]))})")
            continue
        print(f"- {col}:")
        for v, n in vc.items():
            print(f"    {n:>5}  {v}")
    if cfg:
        strata = assign_strata(ann, cfg.get("strata"), cfg.get("strata_field"))
        print("\nGroup assignment with the registry patterns (Case/Control x stratum):")
        for contrast, (case, ctrl) in cfg["contrasts"].items():
            g = assign_groups(ann, case, ctrl, cfg.get("exclude"), cfg.get("group_field")).fillna("unassigned")
            print(f"\n  {contrast}:")
            print(pd_crosstab(strata.fillna("no stratum"), g))
    else:
        print(f"\n{cid} is not in the registry; add it to sphingomap_cns/registry.py to analyse it.")


def pd_crosstab(a, b):
    import pandas as pd
    return pd.crosstab(a, b).to_string()


if __name__ == "__main__":
    sys.exit(main())
