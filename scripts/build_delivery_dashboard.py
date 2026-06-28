"""Build the operations-facing delivery layer from the unified warehouse.

This script demonstrates the "one backbone, many surfaces" pattern: it reads the
same governed marts that power the Streamlit app and the (illustrative) Looker /
AppSheet layers, and emits a lightweight, self-contained HTML dashboard plus a
JSON payload that a Google Apps Script web app can serve to operations teams that
are hard to reach with a heavyweight BI tool.

    python scripts/build_delivery_dashboard.py

Outputs (synthetic data only):
    delivery/gas_webapp/data.json       machine-readable payload (also for GAS)
    delivery/gas_webapp/dashboard.html  standalone interactive dashboard
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from saas_insights.db import query_df  # noqa: E402

OUT = ROOT / "delivery" / "gas_webapp"


def _series(frame) -> dict:
    return {
        "months": frame["month"].astype(str).tolist(),
        "arr": frame["ending_arr_jpy_mn"].round(1).tolist(),
        "growth": frame["arr_growth_yoy_pct"].round(1).tolist(),
        "nrr": frame["nrr_ttm_pct"].round(1).tolist(),
    }


def build_payload() -> dict:
    company = query_df(
        """
        SELECT month, ending_arr_jpy_mn, arr_growth_yoy_pct, nrr_ttm_pct, grr_ttm_pct,
               rule_of_40_pct, magic_number, cac_payback_months, ltv_to_cac
        FROM gtm_company_monthly
        ORDER BY month
        """
    )
    latest = company.iloc[-1]
    segments = query_df(
        """
        SELECT segment, ending_arr_jpy_mn, arr_growth_yoy_pct, nrr_ttm_pct, grr_ttm_pct,
               magic_number, cac_payback_months, ltv_to_cac, win_rate_pct
        FROM gtm_segment_latest
        """
    )
    accounts = query_df(
        """
        SELECT account_name, segment, recommended_play, priority_band,
               ROUND(expected_commercial_value_jpy_mn, 1) AS expected_value_jpy_mn,
               ROUND(data_confidence_pct, 0) AS data_confidence_pct,
               governance_status, next_best_action
        FROM account_positioning
        WHERE priority_band = 'High'
        ORDER BY priority_score DESC
        LIMIT 25
        """
    )
    return {
        "as_of_month": str(latest["month"]),
        "kpis": {
            "arr_jpy_mn": round(float(latest["ending_arr_jpy_mn"]), 1),
            "growth_yoy_pct": float(latest["arr_growth_yoy_pct"]),
            "nrr_ttm_pct": float(latest["nrr_ttm_pct"]),
            "grr_ttm_pct": float(latest["grr_ttm_pct"]),
            "rule_of_40_pct": float(latest["rule_of_40_pct"]),
            "magic_number": float(latest["magic_number"]),
            "cac_payback_months": float(latest["cac_payback_months"]),
            "ltv_to_cac": float(latest["ltv_to_cac"]),
        },
        # Start the series where trailing-twelve-month metrics become valid so the
        # NRR / growth lines have no artificial step from the warm-up period.
        "arr_series": _series(company[company["nrr_ttm_pct"].notna()]),
        "segments": segments.round(2).to_dict(orient="records"),
        "priority_accounts": accounts.to_dict(orient="records"),
    }


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>GTM Ops Dashboard (synthetic)</title>
<style>
  :root { --ink:#1f2933; --muted:#7b8794; --line:#e4e7eb; --accent:#2f6df6; --good:#0a7d4b; }
  * { box-sizing:border-box; }
  body { font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
    margin:0; color:var(--ink); background:#f7f8fa; }
  header { padding:20px 28px; background:#fff; border-bottom:1px solid var(--line); }
  h1 { font-size:20px; margin:0; }
  .sub { color:var(--muted); font-size:13px; margin-top:4px; }
  main { padding:24px 28px; max-width:1180px; margin:0 auto; }
  .cards { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
  .card { background:#fff; border:1px solid var(--line); border-radius:10px; padding:14px 16px; }
  .card .label { color:var(--muted); font-size:12px; }
  .card .value { font-size:24px; font-weight:600; margin-top:4px; }
  .card .bench { font-size:11px; margin-top:4px; }
  .ok { color:var(--good); } .warn { color:#b54708; }
  .panel { background:#fff; border:1px solid var(--line); border-radius:10px;
    padding:16px; margin-top:18px; }
  .panel h2 { font-size:15px; margin:0 0 10px; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th,td { text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); }
  th { color:var(--muted); font-weight:600; }
  .pill { padding:2px 8px; border-radius:999px; font-size:11px; background:#eef2ff; color:#3730a3; }
  .muted { color:var(--muted); font-size:12px; }
  .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
  @media (max-width:780px) { .cards,.grid2 { grid-template-columns:1fr; } }
</style>
</head>
<body>
<header>
  <h1>GTM Operations Dashboard <span class="muted">— synthetic demo</span></h1>
  <div class="sub">One unified backbone, delivered to ops as a lightweight web app ·
    as of <span id="asof"></span></div>
</header>
<main>
  <div class="cards" id="cards"></div>
  <div class="grid2">
    <div class="panel"><h2>ARR &amp; YoY growth</h2><canvas id="arrChart" height="220"></canvas></div>
    <div class="panel"><h2>Net revenue retention (TTM)</h2><canvas id="nrrChart" height="220"></canvas></div>
  </div>
  <div class="panel">
    <h2>Segment economics (latest)</h2>
    <table id="segTable"><thead><tr>
      <th>Segment</th><th>ARR</th><th>Growth</th><th>NRR</th><th>GRR</th>
      <th>Magic #</th><th>CAC payback</th><th>LTV/CAC</th><th>Win rate</th>
    </tr></thead><tbody></tbody></table>
  </div>
  <div class="panel">
    <h2>High-priority accounts — next best action</h2>
    <table id="acctTable"><thead><tr>
      <th>Account</th><th>Segment</th><th>Play</th><th>Expected value</th>
      <th>Data conf.</th><th>Status</th><th>Next best action</th>
    </tr></thead><tbody></tbody></table>
    <p class="muted">Governance: accounts flagged "Evidence required" stay out of Commit
      until the data baseline is reconciled.</p>
  </div>
  <p class="muted">Synthetic data. This page mirrors the Apps Script web app in
    <code>delivery/gas_webapp/</code> that, in production, reads the same BigQuery marts.</p>
</main>
<script>
const DATA = __DATA__;
const yen = v => "¥" + Number(v).toLocaleString(undefined,{maximumFractionDigits:0}) + "M";
document.getElementById("asof").textContent = DATA.as_of_month;

const k = DATA.kpis;
const cards = [
  ["ARR", yen(k.arr_jpy_mn), "synthetic", null],
  ["Growth YoY", k.growth_yoy_pct.toFixed(0)+"%", "vs ~30% healthy", k.growth_yoy_pct>=30],
  ["NRR (TTM)", k.nrr_ttm_pct.toFixed(0)+"%", "vs 110% best-in-class", k.nrr_ttm_pct>=110],
  ["GRR (TTM)", k.grr_ttm_pct.toFixed(0)+"%", "vs 90% target", k.grr_ttm_pct>=90],
  ["Rule of 40", k.rule_of_40_pct.toFixed(0), "vs 40 threshold", k.rule_of_40_pct>=40],
  ["Magic Number", k.magic_number.toFixed(2), "vs 0.75 efficient", k.magic_number>=0.75],
  ["CAC payback", k.cac_payback_months.toFixed(0)+" mo", "vs <18 mo", k.cac_payback_months<=18],
  ["LTV / CAC", k.ltv_to_cac.toFixed(1)+"x", "vs 3x+ healthy", k.ltv_to_cac>=3],
];
document.getElementById("cards").innerHTML = cards.map(c => {
  const cls = c[3]===null ? "" : (c[3] ? "ok" : "warn");
  return `<div class="card"><div class="label">${c[0]}</div>
    <div class="value">${c[1]}</div><div class="bench ${cls}">${c[2]}</div></div>`;
}).join("");

// Lightweight self-contained charts using the native Canvas API (no libraries,
// works fully offline). Demonstrates the same delivery pattern a GAS web app uses.
function setup(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 520, h = canvas.height;
  canvas.width = w * dpr; canvas.height = h * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  return { ctx, w, h };
}
const PAD = { l: 44, r: 44, t: 14, b: 26 };
function axes(ctx, w, h) {
  ctx.strokeStyle = "#e4e7eb"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(PAD.l, h - PAD.b); ctx.lineTo(w - PAD.r, h - PAD.b); ctx.stroke();
}
function drawArr(canvas, labels, bars, line) {
  const { ctx, w, h } = setup(canvas); axes(ctx, w, h);
  const ph = h - PAD.t - PAD.b, pw = w - PAD.l - PAD.r;
  const bmax = Math.max(...bars) * 1.1;
  const lmin = Math.min(...line), lmax = Math.max(...line);
  const bw = pw / bars.length * 0.7;
  ctx.fillStyle = "#2f6df6";
  bars.forEach((v, i) => {
    const x = PAD.l + pw * (i + 0.5) / bars.length - bw / 2;
    const bh = ph * v / bmax;
    ctx.fillRect(x, h - PAD.b - bh, bw, bh);
  });
  ctx.strokeStyle = "#0a7d4b"; ctx.lineWidth = 2; ctx.beginPath();
  line.forEach((v, i) => {
    const x = PAD.l + pw * (i + 0.5) / bars.length;
    const y = h - PAD.b - ph * (v - lmin) / ((lmax - lmin) || 1);
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.stroke();
  ctx.fillStyle = "#7b8794"; ctx.font = "10px sans-serif"; ctx.textAlign = "center";
  ctx.fillText(labels[0], PAD.l + 10, h - 8);
  ctx.fillText(labels[labels.length - 1], w - PAD.r - 10, h - 8);
}
function drawLine(canvas, labels, series, floor) {
  const { ctx, w, h } = setup(canvas); axes(ctx, w, h);
  const ph = h - PAD.t - PAD.b, pw = w - PAD.l - PAD.r;
  const lo = Math.min(floor, ...series), hi = Math.max(...series);
  ctx.strokeStyle = "#9aa5b1"; ctx.setLineDash([3, 3]); ctx.beginPath();
  const y100 = h - PAD.b - ph * (100 - lo) / ((hi - lo) || 1);
  ctx.moveTo(PAD.l, y100); ctx.lineTo(w - PAD.r, y100); ctx.stroke(); ctx.setLineDash([]);
  ctx.strokeStyle = "#2f6df6"; ctx.lineWidth = 2; ctx.beginPath();
  series.forEach((v, i) => {
    const x = PAD.l + pw * i / (series.length - 1);
    const y = h - PAD.b - ph * (v - lo) / ((hi - lo) || 1);
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.stroke();
  ctx.fillStyle = "#7b8794"; ctx.font = "10px sans-serif"; ctx.textAlign = "left";
  ctx.fillText("100%", w - PAD.r - 2, y100 - 4);
}
try {
  drawArr(document.getElementById("arrChart"),
    DATA.arr_series.months, DATA.arr_series.arr, DATA.arr_series.growth);
  drawLine(document.getElementById("nrrChart"),
    DATA.arr_series.months, DATA.arr_series.nrr, 95);
} catch (e) { /* charts are progressive enhancement */ }

const segBody = document.querySelector("#segTable tbody");
segBody.innerHTML = DATA.segments.map(s => `<tr>
  <td>${s.segment}</td><td>${yen(s.ending_arr_jpy_mn)}</td>
  <td>${s.arr_growth_yoy_pct.toFixed(0)}%</td><td>${s.nrr_ttm_pct.toFixed(0)}%</td>
  <td>${s.grr_ttm_pct.toFixed(0)}%</td><td>${s.magic_number.toFixed(2)}</td>
  <td>${s.cac_payback_months.toFixed(0)} mo</td><td>${s.ltv_to_cac.toFixed(1)}x</td>
  <td>${s.win_rate_pct.toFixed(0)}%</td></tr>`).join("");

const acctBody = document.querySelector("#acctTable tbody");
acctBody.innerHTML = DATA.priority_accounts.map(a => `<tr>
  <td>${a.account_name}</td><td>${a.segment}</td>
  <td><span class="pill">${a.recommended_play}</span></td>
  <td>${yen(a.expected_value_jpy_mn)}</td><td>${a.data_confidence_pct}%</td>
  <td>${a.governance_status}</td><td>${a.next_best_action}</td></tr>`).join("");
</script>
</body>
</html>
"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    (OUT / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    (OUT / "dashboard.html").write_text(html, "utf-8")

    # Synthetic fallback for the Apps Script web app (used when GCP_PROJECT is unset).
    sample_gs = (
        "// Auto-generated by scripts/build_delivery_dashboard.py — synthetic fallback\n"
        "// payload for the Apps Script web app when BigQuery is not configured.\n"
        "const SAMPLE_PAYLOAD = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n"
    )
    (OUT / "SamplePayload.gs").write_text(sample_gs, "utf-8")

    print(f"wrote {OUT / 'data.json'}")
    print(f"wrote {OUT / 'dashboard.html'}")
    print(f"wrote {OUT / 'SamplePayload.gs'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
