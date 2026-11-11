"""Download and parse NCBI GEO series.

Two routes:

* **RNA-seq** - NCBI re-processes public human RNA-seq series into a uniform
  gene-level raw count matrix (GRCh38.p13, Entrez Gene IDs). We download that
  matrix plus NCBI's gene annotation table and map IDs to symbols.
* **Microarray** - the series matrix holds the submitter-normalised values; the
  platform (GPL) annotation maps probes to gene symbols.

Sample annotations always come from the series matrix header.
"""
from __future__ import annotations

import gzip
import io
import re
import shutil
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

from .genesets import ALIASES

FTP = "https://ftp.ncbi.nlm.nih.gov/geo"
GEO_DL = "https://www.ncbi.nlm.nih.gov/geo/download/"
NCBI_ANNOT = "Human.GRCh38.p13.annot.tsv.gz"
UA = {"User-Agent": "sphingomap-cns (+https://github.com/DhruvASharma2004)"}


# ----------------------------------------------------------------------------- download
def _stub(acc: str) -> str:
    """GSE5281 -> GSE5nnn, GSE153960 -> GSE153nnn, GPL570 -> GPLnnn."""
    prefix, num = re.match(r"([A-Z]+)(\d+)", acc).groups()
    return f"{prefix}{num[:-3]}nnn" if len(num) > 3 else f"{prefix}nnn"


def download(url: str, dest: Path, overwrite: bool = False) -> Path:
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 0 and not overwrite:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as fh:
        shutil.copyfileobj(r, fh)
    tmp.rename(dest)
    return dest


def series_matrix_urls(gse: str) -> list[str]:
    """All series-matrix files for a GSE (multi-platform series have several)."""
    base = f"{FTP}/series/{_stub(gse)}/{gse}/matrix/"
    try:
        req = urllib.request.Request(base, headers=UA)
        html = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
        names = sorted(set(re.findall(rf'href="({gse}[^"]*series_matrix\.txt\.gz)"', html)))
        if names:
            return [base + n for n in names]
    except urllib.error.URLError:
        pass
    return [base + f"{gse}_series_matrix.txt.gz"]


def fetch_series(gse: str, datadir: str | Path, platform: str, gpl: str | None = None) -> dict[str, list[Path] | Path]:
    """Download everything needed for one GSE into ``datadir/gse``."""
    d = Path(datadir) / gse
    out: dict = {"series_matrix": [download(u, d / u.rsplit("/", 1)[1]) for u in series_matrix_urls(gse)]}
    if platform == "rnaseq":
        fname = f"{gse}_raw_counts_GRCh38.p13_NCBI.tsv.gz"
        out["counts"] = download(f"{GEO_DL}?type=rnaseq_counts&acc={gse}&format=file&file={fname}", d / fname)
        out["gene_annot"] = download(f"{GEO_DL}?type=rnaseq_counts&format=file&file={NCBI_ANNOT}",
                                     Path(datadir) / NCBI_ANNOT)
    elif gpl:
        out["platform"] = fetch_platform(gpl, datadir)
    return out


def fetch_platform(gpl: str, datadir: str | Path) -> Path:
    """GPL annotation: curated .annot.gz if GEO has one, else the full SOFT table."""
    d = Path(datadir) / "platforms"
    try:
        return download(f"{FTP}/platforms/{_stub(gpl)}/{gpl}/annot/{gpl}.annot.gz", d / f"{gpl}.annot.gz")
    except urllib.error.HTTPError:
        url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={gpl}&targ=self&form=text&view=data"
        return download(url, d / f"{gpl}.soft.txt")


# ----------------------------------------------------------------------------- parsing
def _open_text(path: Path):
    path = Path(path)
    with open(path, "rb") as fh:
        magic = fh.read(2)
    if magic == b"\x1f\x8b":
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", errors="replace")
    return open(path, encoding="utf-8", errors="replace")


def _split(line: str) -> list[str]:
    return [c.strip().strip('"') for c in line.rstrip("\n").split("\t")]


def parse_series_matrix(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (sample annotation table, expression table [probes x GSM]).

    Annotation columns: ``title``, ``source``, ``platform`` and one column per
    characteristics key (``tissue``, ``disease state``...). Characteristics
    without a ``key: value`` form are kept as ``characteristics_<n>``.
    """
    meta: dict[str, list[str]] = {}
    chars: list[list[str]] = []
    table_lines: list[str] = []
    in_table = False
    with _open_text(path) as fh:
        for line in fh:
            if line.startswith("!series_matrix_table_begin"):
                in_table = True
                continue
            if line.startswith("!series_matrix_table_end"):
                in_table = False
                continue
            if in_table:
                table_lines.append(line)
            elif line.startswith("!Sample_"):
                cells = _split(line)
                key = cells[0][len("!Sample_"):]
                if key.startswith("characteristics"):
                    chars.append(cells[1:])
                elif key not in meta:
                    meta[key] = cells[1:]
    gsm = meta.get("geo_accession")
    if not gsm:
        raise ValueError(f"No !Sample_geo_accession line in {path}")
    ann = pd.DataFrame(index=pd.Index(gsm, name="sample"))
    for src, dst in (("title", "title"), ("source_name_ch1", "source"), ("platform_id", "platform"),
                     ("description", "description")):
        if src in meta:
            ann[dst] = meta[src]
    for i, row in enumerate(chars):
        keys = {c.split(":", 1)[0].strip().lower() for c in row if ":" in c}
        if len(keys) == 1:
            k = keys.pop()
            col = k if k not in ann.columns else f"{k}_{i}"
            ann[col] = [c.split(":", 1)[1].strip() if ":" in c else "" for c in row]
        else:  # mixed keys on one line (happens in GEO) - split per sample
            for j, c in enumerate(row):
                if ":" in c:
                    k, v = (s.strip() for s in c.split(":", 1))
                    k = k.lower()
                    if k not in ann.columns:
                        ann[k] = ""
                    ann.iloc[j, ann.columns.get_loc(k)] = v
                elif c:
                    col = f"characteristics_{i}"
                    if col not in ann.columns:
                        ann[col] = ""
                    ann.iloc[j, ann.columns.get_loc(col)] = c
    ann = ann.fillna("")
    expr = pd.DataFrame()
    if len(table_lines) > 1:
        expr = pd.read_csv(io.StringIO("".join(table_lines)), sep="\t", index_col=0)
        expr.index = expr.index.astype(str)
        expr = expr.apply(pd.to_numeric, errors="coerce")
    return ann, expr


def load_series(paths: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    anns, exprs = zip(*(parse_series_matrix(p) for p in paths), strict=True)
    ann = pd.concat(anns)
    ann = ann[~ann.index.duplicated()].fillna("")
    exprs = [e for e in exprs if not e.empty]
    expr = pd.concat(exprs, axis=1) if exprs else pd.DataFrame()
    return ann, expr


SYMBOL_COLUMNS = ["Gene symbol", "Gene Symbol", "GENE_SYMBOL", "Symbol", "ILMN_Gene", "gene_symbol", "SYMBOL"]


def parse_platform(path: str | Path) -> pd.Series:
    """Probe ID -> gene symbol. Probes mapping to several genes ('A /// B') are dropped."""
    lines: list[str] = []
    in_table, saw_marker = False, False
    with _open_text(path) as fh:
        for line in fh:
            if line.startswith("!platform_table_begin"):
                in_table, saw_marker = True, True
                continue
            if line.startswith("!platform_table_end"):
                break
            if in_table:
                lines.append(line)
    if not saw_marker:  # plain TSV with '#' comments
        with _open_text(path) as fh:
            lines = [ln for ln in fh if not ln.startswith(("#", "^", "!"))]
    tab = pd.read_csv(io.StringIO("".join(lines)), sep="\t", dtype=str, low_memory=False)
    col = next((c for c in SYMBOL_COLUMNS if c in tab.columns), None)
    if col is None:
        raise ValueError(f"No gene-symbol column in {path}; columns: {list(tab.columns)[:15]}")
    m = tab.set_index(tab.columns[0])[col].dropna().astype(str).str.strip()
    m = m[(m != "") & ~m.str.contains("///|//|,")]
    m.index = m.index.astype(str)
    return m


def harmonize_symbols(expr: pd.DataFrame) -> pd.DataFrame:
    """Upper-case, map retired symbols to current ones, average duplicates."""
    expr = expr.rename(index=lambda g: ALIASES.get(str(g).upper(), str(g).upper()))
    if expr.index.duplicated().any():
        expr = expr.groupby(level=0).mean()
    return expr


def probes_to_genes(expr: pd.DataFrame, probe_map: pd.Series) -> pd.DataFrame:
    """Collapse probes to genes, keeping the probe with the highest mean signal."""
    common = expr.index.intersection(probe_map.index)
    if len(common) == 0:
        raise ValueError("No probe IDs in the expression table match the platform annotation")
    e = expr.loc[common].copy()
    e["__sym"] = probe_map.loc[common].map(lambda g: ALIASES.get(g.upper(), g.upper())).values
    e["__mean"] = e.drop(columns="__sym").mean(axis=1)
    e = e.sort_values("__mean", ascending=False).drop_duplicates("__sym")
    return e.set_index("__sym").drop(columns="__mean").rename_axis("gene")


def load_ncbi_counts(counts_path: str | Path, annot_path: str | Path) -> pd.DataFrame:
    """NCBI-generated raw counts (GeneID x GSM) -> symbol-indexed counts."""
    counts = pd.read_csv(counts_path, sep="\t", index_col=0)
    annot = pd.read_csv(annot_path, sep="\t", index_col=0, usecols=[0, 1], dtype={0: str})
    sym = annot.iloc[:, 0].astype(str)
    sym.index = sym.index.astype(str)
    counts.index = counts.index.astype(str)
    counts = counts.loc[counts.index.intersection(sym.index)]
    counts.index = sym.loc[counts.index].values
    counts = counts.rename(index=lambda g: ALIASES.get(g.upper(), g.upper()))
    return counts.groupby(level=0).sum().rename_axis("gene")
