"""
Metrics and usage dashboard routes for the Vue API.
"""

import logging

from flask import request, jsonify, Response

from src.metrics import get_daily_counts, get_totals, get_counts_last_n_days

logger = logging.getLogger(__name__)


def register_metrics_routes(bp):
    @bp.route("/metrics/summary", methods=["GET"])
    def metrics_summary():
        """Public: totals and today's counts (UTC)."""
        try:
            day = request.args.get("date")
            daily = get_daily_counts(day)
            totals = get_totals()
            payload = {"daily": daily, "totals": totals}
            resp = jsonify(payload)
            resp.headers["Cache-Control"] = "public, max-age=60"
            return resp
        except Exception as e:
            logger.warning(f"metrics_summary error: {e}")
            return jsonify({"error": "metrics unavailable"}), 503

    @bp.route("/metrics", methods=["GET"])
    def metrics_dashboard():
        try:
            html = _get_metrics_html()
            return Response(html, mimetype="text/html")
        except Exception as e:
            return jsonify({"error": "metrics dashboard unavailable", "detail": str(e)}), 503

    @bp.route("/metrics/daily", methods=["GET"])
    def metrics_daily():
        """Public: single day's counts (UTC)."""
        try:
            day = request.args.get("date")
            payload = get_daily_counts(day)
            resp = jsonify(payload)
            resp.headers["Cache-Control"] = "public, max-age=60"
            return resp
        except Exception as e:
            logger.warning(f"metrics_daily error: {e}")
            return jsonify({"error": "metrics unavailable"}), 503

    @bp.route("/metrics/series", methods=["GET"])
    def metrics_series():
        """Public: per-day counts for the last N days (UTC)."""
        try:
            try:
                days = int(request.args.get("days", 30))
            except Exception:
                days = 30
            end_date = request.args.get("end")
            series = get_counts_last_n_days(days=days, end_date=end_date)
            payload = {"days": days, "end": end_date, "series": series}
            resp = jsonify(payload)
            resp.headers["Cache-Control"] = "public, max-age=60"
            return resp
        except Exception as e:
            logger.warning(f"metrics_series error: {e}")
            return jsonify({"error": "metrics unavailable"}), 503


def _get_metrics_html():
    """Return the metrics dashboard HTML (inline to avoid huge literal in route)."""
    # Inline copy of the dashboard from vue_api_endpoints_updated
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" "
        "content=\"width=device-width, initial-scale=1\"><title>CaseStrainer Usage Metrics</title>"
        "<link rel=\"preconnect\" href=\"https://cdn.jsdelivr.net\"><script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>"
        "<style>:root{--bg:#0b1120;--panel:#111827;--text:#e5e7eb;--muted:#9ca3af;--accent:#60a5fa;} "
        "body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,sans-serif;} "
        ".wrap{max-width:1100px;margin:0 auto;padding:24px;} .header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;} "
        ".controls input{background:#0f172a;border:1px solid #1f2937;color:var(--text);padding:8px;border-radius:8px;width:90px;} "
        ".controls button{background:var(--accent);color:#001;border:none;padding:8px 12px;border-radius:8px;cursor:pointer;} "
        ".grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;} .panel{background:var(--panel);border:1px solid #1f2937;border-radius:12px;padding:16px;} "
        ".cards{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;} "
        ".card{background:#0b1220;border:1px solid #1f2937;border-radius:12px;padding:12px;} "
        ".card .label{font-size:12px;color:var(--muted);} .card .value{font-size:24px;font-weight:700;}</style>"
        "<meta http-equiv=\"Cache-Control\" content=\"no-cache\"/><meta name=\"robots\" content=\"noindex\"/>"
        "<script>"
        "async function fetchJSON(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);return await r.json();}"
        "function formatNum(n){return (n||0).toLocaleString();}"
        "function makeChart(ctx,label,labels,data,color){return new Chart(ctx,{type:'line',data:{labels,datasets:[{label,data,borderColor:color,backgroundColor:color+'33',fill:true,tension:0.25,pointRadius:0}]},options:{scales:{x:{ticks:{color:'#9ca3af'}},y:{ticks:{color:'#9ca3af'},beginAtZero:true}}});}"
        "async function loadMetrics(){const days=parseInt(document.getElementById('days').value||'30',10);"
        "const base=window.location.origin+window.location.pathname.replace(/\\\\/metrics$/,'');"
        "const [series,summary]=await Promise.all([fetchJSON(base+'/metrics/series?days='+days),fetchJSON(base+'/metrics/summary')]);"
        "const labels=series.series.map(p=>p.date);const docs=series.series.map(p=>p.documents);const cites=series.series.map(p=>p.citations);"
        "document.getElementById('docsToday').textContent=formatNum(summary.daily.documents);document.getElementById('citesToday').textContent=formatNum(summary.daily.citations);"
        "document.getElementById('docsTotal').textContent=formatNum(summary.totals.documents);document.getElementById('citesTotal').textContent=formatNum(summary.totals.citations);"
        "window._docsChart&&window._docsChart.destroy();window._citesChart&&window._citesChart.destroy();"
        "window._docsChart=makeChart(document.getElementById('docsChart'),'Documents/day',labels,docs,'#60a5fa');"
        "window._citesChart=makeChart(document.getElementById('citesChart'),'Citations/day',labels,cites,'#34d399');}"
        "window.addEventListener('DOMContentLoaded',()=>{document.getElementById('refresh').onclick=()=>loadMetrics().catch(()=>{});loadMetrics().catch(()=>{});});"
        "</script></head><body><div class=\"wrap\"><div class=\"header\"><div class=\"title\">CaseStrainer Usage Metrics</div>"
        "<div class=\"controls\"><input id=\"days\" type=\"number\" min=\"1\" max=\"365\" value=\"30\"/><button id=\"refresh\">Refresh</button></div></div>"
        "<div class=\"cards\"><div class=\"card\"><div class=\"label\">Documents today</div><div id=\"docsToday\" class=\"value\">-</div></div>"
        "<div class=\"card\"><div class=\"label\">Citations today</div><div id=\"citesToday\" class=\"value\">-</div></div>"
        "<div class=\"card\"><div class=\"label\">Documents total</div><div id=\"docsTotal\" class=\"value\">-</div></div>"
        "<div class=\"card\"><div class=\"label\">Citations total</div><div id=\"citesTotal\" class=\"value\">-</div></div></div>"
        "<div class=\"grid\"><div class=\"panel\"><h2>Documents</h2><canvas id=\"docsChart\" height=\"120\"></canvas></div>"
        "<div class=\"panel\"><h2>Citations</h2><canvas id=\"citesChart\" height=\"120\"></canvas></div></div>"
        "<div style=\"margin-top:16px;color:#9ca3af;\">API: <a href=\"./metrics/summary\">/metrics/summary</a> | <a href=\"./metrics/series\">/metrics/series</a></div></div></body></html>"
    )
