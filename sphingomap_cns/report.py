"""Self-contained interactive HTML atlas (no external assets; figures embedded)."""
from __future__ import annotations

import base64
import html
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import __version__
from .genesets import MODULES, gene_to_module
from .scores import score_label


def _img(path: Path) -> str:
    if not path.exists():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{b64}" alt="{html.escape(path.stem)}">'


def _clean(v):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return None
    return round(float(v), 4)


def write_atlas_html(out: Path, title: str, runs: pd.DataFrame, G: pd.DataFrame, Q: pd.DataFrame,
                     LFC: pd.DataFrame, SG: pd.DataFrame, SQ: pd.DataFrame, meta: pd.DataFrame) -> Path:
    mod = gene_to_module()
    rows = []
    for g in G.index:
        r = {"gene": g, "module": MODULES[mod[g]]["label"], "kind": MODULES[mod[g]]["kind"],
             "g": [_clean(x) for x in G.loc[g]], "q": [_clean(x) for x in Q.loc[g]],
             "lfc": [_clean(x) for x in LFC.loc[g]]}
        if not meta.empty:
            for contrast, m in meta.groupby("contrast"):
                if g in m.index:
                    r[f"meta_{contrast}"] = _clean(m.loc[g, "g_meta"])
                    r[f"metaq_{contrast}"] = _clean(m.loc[g, "fdr"])
        rows.append(r)
    contrasts = list(meta["contrast"].unique()) if not meta.empty else []
    data = {"cols": list(G.columns), "rows": rows, "contrasts": contrasts,
            "modules": [m["label"] for m in MODULES.values()]}

    run_rows = []
    for _, r in runs.iterrows():
        ok = r["status"] == "ok"
        detail = (f'<a href="{html.escape(str(r["dir"]))}/REPORT.md">report</a>' if ok
                  else html.escape(f"{r['status']}: {r.get('reason', '')}"))
        covs = ", ".join(r["covariates"]) if ok and isinstance(r["covariates"], list) else ""
        run_rows.append(
            f"<tr><td>{html.escape(str(r['contrast']))}</td><td>{html.escape(str(r['cohort']))}</td>"
            f"<td>{html.escape(str(r['stratum']))}</td>"
            f"<td class=n>{int(r['n_case']) if ok else ''}</td><td class=n>{int(r['n_control']) if ok else ''}</td>"
            f"<td>{covs}</td><td>{detail}</td></tr>")

    score_rows = []
    for s in SG.index:
        cells = "".join(
            f"<td class=n style='background:{_div_color(v)}'>{'' if pd.isna(v) else f'{v:+.2f}'}"
            f"{'*' if pd.notna(q) and q < 0.05 else ''}</td>" for v, q in zip(SG.loc[s], SQ.loc[s], strict=True))
        score_rows.append(f"<tr><th>{html.escape(score_label(s))}</th>{cells}</tr>")
    score_head = "".join(f"<th class=rot><span>{html.escape(c)}</span></th>" for c in SG.columns)

    figs = out / "figures"
    meta_imgs = "".join(f"<figure>{_img(p)}</figure>" for p in sorted(figs.glob("pathway_meta_*.png")))
    page = TEMPLATE.format(
        title=html.escape(title), version=__version__, runs="".join(run_rows),
        atlas_genes=_img(figs / "atlas_genes.png"), atlas_scores=_img(figs / "atlas_scores.png"),
        meta_imgs=meta_imgs, score_head=score_head, score_rows="".join(score_rows),
        data=json.dumps(data).replace("</", "<\\/"))
    path = out / "atlas.html"
    path.write_text(page, encoding="utf-8")
    return path


def _div_color(v, vmax=1.5) -> str:
    if v is None or pd.isna(v):
        return "transparent"
    t = max(-1.0, min(1.0, v / vmax))
    a = abs(t) * 0.75
    return f"rgba(202,64,52,{a:.2f})" if t > 0 else f"rgba(42,120,214,{a:.2f})"


TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{ --ink:#1d1d1b; --muted:#6b6a65; --line:#e4e3de; --bg:#fcfcfb; --accent:#2a78d6; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  color:var(--ink); background:var(--bg); }}
main {{ max-width:1180px; margin:0 auto; padding:32px 24px 64px; }}
h1 {{ font-size:26px; margin:0 0 4px; }} h2 {{ font-size:18px; margin:40px 0 10px; border-bottom:1px solid var(--line);
  padding-bottom:6px; }}
.sub {{ color:var(--muted); margin:0 0 20px; }}
table {{ border-collapse:collapse; width:100%; font-size:12.5px; }}
th, td {{ padding:5px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:bottom; }}
td.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
th.rot {{ height:150px; white-space:nowrap; padding:0 2px; }}
th.rot span {{ display:inline-block; transform:rotate(-55deg); transform-origin:left bottom; width:22px;
  font-weight:500; font-size:11px; }}
figure {{ margin:16px 0; }} img {{ max-width:100%; height:auto; }}
.controls {{ display:flex; gap:10px; flex-wrap:wrap; margin:8px 0 12px; }}
input, select {{ font:inherit; padding:5px 8px; border:1px solid var(--line); border-radius:6px; background:white; }}
#genes td.c {{ text-align:center; font-size:11.5px; min-width:44px; cursor:default; }}
#genes th.sort {{ cursor:pointer; }} #genes th.sort:hover {{ color:var(--accent); }}
.scroll {{ overflow-x:auto; }} .scroll table {{ margin-right:140px; width:auto; }}
.note {{ color:var(--muted); font-size:12.5px; }}
#tip {{ position:fixed; pointer-events:none; background:#1d1d1b; color:white; font-size:12px; padding:6px 8px;
  border-radius:6px; display:none; z-index:10; max-width:320px; }}
</style></head>
<body><main>
<h1>{title}</h1>
<p class="sub">Sphingolipid, ceramide and lipid-peroxidation gene networks across public ALS, FTD and AD
transcriptomes &middot; sphingomap-CNS v{version}</p>

<h2>Gene atlas</h2>
<p class="note">Hedges' g, case vs control, per cohort stratum. Red = higher in disease, blue = lower.
* FDR &lt; 0.05, ** FDR &lt; 0.01 within the stratum. Hover a cell for details; click a column header to sort.</p>
<div class="controls">
  <input id="q" placeholder="Search gene..." size="16">
  <select id="mod"><option value="">All modules</option></select>
  <select id="kind"><option value="">Pathway + context</option><option value="sphingolipid">Sphingolipid pathway only</option>
  <option value="context">Neuroinflammatory context only</option></select>
  <label><input type="checkbox" id="sigonly"> significant somewhere</label>
</div>
<div class="scroll"><table id="genes"><thead></thead><tbody></tbody></table></div>
<div id="tip"></div>

<h2>Module scores</h2>
<div class="scroll"><table><thead><tr><th></th>{score_head}</tr></thead><tbody>{score_rows}</tbody></table></div>
<p class="note">Hedges' g of per-sample module scores (mean z vs controls). * FDR &lt; 0.05.</p>

<h2>Figures</h2>
<figure>{atlas_genes}</figure>
<figure>{atlas_scores}</figure>
{meta_imgs}

<h2>Comparisons</h2>
<table><thead><tr><th>Contrast</th><th>Cohort</th><th>Stratum</th><th>Case</th><th>Control</th><th>Covariates</th>
<th>Details</th></tr></thead><tbody>{runs}</tbody></table>

<h2>Reading notes</h2>
<p class="note">Bulk post-mortem tissue mixes cell types, so changes can reflect neuron loss or gliosis rather than
per-cell regulation. Meta-analysis pools strata of one disease; brain regions from the same donors are not independent,
so pooled p-values are optimistic. Transcript changes are hypotheses for lipid measurement, not lipid measurements.</p>
</main>
<script>
const D = {data};
const tip = document.getElementById('tip');
const modSel = document.getElementById('mod');
D.modules.forEach(m => {{ const o = document.createElement('option'); o.value = m; o.textContent = m; modSel.appendChild(o); }});
let sortKey = null, sortDir = -1;
function color(v) {{
  if (v === null) return 'transparent';
  const t = Math.max(-1, Math.min(1, v / 1.5)), a = (Math.abs(t) * 0.75).toFixed(2);
  return t > 0 ? `rgba(202,64,52,${{a}})` : `rgba(42,120,214,${{a}})`;
}}
function fmt(v) {{ return v === null || v === undefined ? '' : (v > 0 ? '+' : '') + v.toFixed(2); }}
function star(q) {{ return q !== null && q !== undefined ? (q < 0.01 ? '**' : q < 0.05 ? '*' : '') : ''; }}
function head() {{
  const metaCols = D.contrasts.map(c => `<th class="sort rot" data-k="meta_${{c}}"><span>${{c}} meta g</span></th>`).join('');
  const cols = D.cols.map((c, i) => `<th class="sort rot" data-k="${{i}}"><span>${{c}}</span></th>`).join('');
  document.querySelector('#genes thead').innerHTML =
    `<tr><th class="sort" data-k="gene">Gene</th><th class="sort" data-k="module">Module</th>${{metaCols}}${{cols}}</tr>`;
  document.querySelectorAll('#genes th.sort').forEach(th => th.onclick = () => {{
    const k = th.dataset.k; sortDir = sortKey === k ? -sortDir : -1; sortKey = k; render();
  }});
}}
function val(r, k) {{
  if (k === 'gene' || k === 'module') return r[k];
  if (k.startsWith('meta_')) return r[k] ?? null;
  return r.g[+k];
}}
function render() {{
  const q = document.getElementById('q').value.trim().toUpperCase();
  const m = modSel.value, kind = document.getElementById('kind').value, sig = document.getElementById('sigonly').checked;
  let rows = D.rows.filter(r => (!q || r.gene.includes(q)) && (!m || r.module === m) && (!kind || r.kind === kind)
    && (!sig || r.q.some(x => x !== null && x < 0.05)));
  if (sortKey !== null) rows = rows.slice().sort((a, b) => {{
    const x = val(a, sortKey), y = val(b, sortKey);
    if (x === null || x === undefined) return 1; if (y === null || y === undefined) return -1;
    if (typeof x === 'string') return -sortDir * x.localeCompare(y);
    return sortDir * (x - y);
  }});
  document.querySelector('#genes tbody').innerHTML = rows.map(r => {{
    const meta = D.contrasts.map(c => `<td class="c" style="background:${{color(r['meta_' + c] ?? null)}}"
      data-t="${{r.gene}} &middot; ${{c}} meta-analysis: g ${{fmt(r['meta_' + c])}}, FDR ${{(r['metaq_' + c] ?? NaN).toExponential(1)}}">
      ${{fmt(r['meta_' + c])}}${{star(r['metaq_' + c])}}</td>`).join('');
    const cells = r.g.map((v, i) => `<td class="c" style="background:${{color(v)}}"
      data-t="${{r.gene}} &middot; ${{D.cols[i]}}: g ${{fmt(v)}}, log2FC ${{fmt(r.lfc[i])}}, FDR ${{r.q[i] === null ? 'n/a' : r.q[i].toExponential(1)}}">
      ${{fmt(v)}}${{star(r.q[i])}}</td>`).join('');
    return `<tr><td><b>${{r.gene}}</b></td><td>${{r.module}}</td>${{meta}}${{cells}}</tr>`;
  }}).join('');
}}
document.addEventListener('mousemove', e => {{
  const t = e.target.closest('td[data-t]');
  if (!t) {{ tip.style.display = 'none'; return; }}
  tip.innerHTML = t.dataset.t; tip.style.display = 'block';
  tip.style.left = Math.min(e.clientX + 12, innerWidth - 330) + 'px'; tip.style.top = (e.clientY + 14) + 'px';
}});
['q', 'mod', 'kind', 'sigonly'].forEach(id => document.getElementById(id).addEventListener('input', render));
head(); render();
</script></body></html>
"""
