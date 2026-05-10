from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from ..models.results import SuiteResult, CheckStatus

_CHECK_CATEGORIES = {
    "Completeness": ["not_null", "not_empty", "completeness_rate"],
    "Uniqueness":   ["unique", "duplicate_count"],
    "Conformity":   ["email_format", "phone_format", "url_format", "regex_match",
                     "max_length", "min_length", "no_trailing_spaces"],
    "Validity":     ["min_value", "max_value", "between", "not_negative", "date_format", "in_set"],
    "Consistency":  ["referential_integrity", "no_cross_table_duplicates"],
}


def _build_context(result: SuiteResult) -> dict:
    duration = (
        round((result.completed_at - result.started_at).total_seconds(), 2)
        if result.completed_at else 0
    )

    # ── per-table metrics ────────────────────────────────────────────────────
    table_data = []
    for table, rows in result.table_stats.items():
        tr = [r for r in result.results if r.table == table]
        passed = sum(1 for r in tr if r.status == CheckStatus.PASS)
        failed = sum(1 for r in tr if r.status == CheckStatus.FAIL)
        errors = sum(1 for r in tr if r.status == CheckStatus.ERROR)
        total  = len(tr)
        rate   = round(passed / total * 100, 1) if total else 0
        fields = len({r.field for r in tr})
        table_data.append({
            "name":   table,
            "rows":   rows,
            "fields": fields,
            "checks": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "rate":   rate,
            "rate_color": _rate_color(rate),
        })

    # ── per-category metrics ─────────────────────────────────────────────────
    category_data = []
    for cat, check_types in _CHECK_CATEGORIES.items():
        tr = [r for r in result.results if r.check_type in check_types]
        if not tr:
            continue
        passed = sum(1 for r in tr if r.status == CheckStatus.PASS)
        failed = sum(1 for r in tr if r.status == CheckStatus.FAIL)
        total  = len(tr)
        rate   = round(passed / total * 100, 1) if total else 0
        category_data.append({
            "name":   cat,
            "total":  total,
            "passed": passed,
            "failed": failed,
            "rate":   rate,
            "rate_color": _rate_color(rate),
        })

    # ── top failures ─────────────────────────────────────────────────────────
    failures = [r for r in result.results if r.status == CheckStatus.FAIL]

    # ── field-level summary (unique fields checked) ──────────────────────────
    unique_fields   = len({(r.table, r.field) for r in result.results})
    total_rows_scanned = sum(result.table_stats.values())

    return {
        "result":              result,
        "generated_at":        datetime.now().strftime("%d %b %Y, %H:%M"),
        "duration":            duration,
        "total_rows_scanned":  total_rows_scanned,
        "unique_fields":       unique_fields,
        "table_data":          table_data,
        "category_data":       category_data,
        "failures":            failures,
        "pass_rate_color":     _rate_color(result.pass_rate),
    }


def _rate_color(rate: float) -> str:
    if rate >= 90:
        return "#16a34a"
    if rate >= 70:
        return "#ca8a04"
    return "#dc2626"


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ result.suite_name }} — TestNucleus</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 14px; background: #fff; color: #111; line-height: 1.5; }
    a    { color: inherit; text-decoration: none; }
    .page { max-width: 1120px; margin: 0 auto; padding: 52px 32px 80px; }

    /* ── header ── */
    .header { border-bottom: 1px solid #e5e5e5; padding-bottom: 20px; margin-bottom: 36px; display: flex; justify-content: space-between; align-items: flex-end; }
    .header h1  { font-size: 20px; font-weight: 600; letter-spacing: -.02em; }
    .header .meta { font-size: 12px; color: #999; text-align: right; line-height: 1.8; }
    .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border: 1px solid #e5e5e5; border-radius: 4px; color: #555; margin-left: 6px; }

    /* ── section titles ── */
    .section-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; color: #aaa; margin-bottom: 12px; }

    /* ── summary cards ── */
    .cards { display: grid; grid-template-columns: repeat(8, 1fr); gap: 0; border: 1px solid #e5e5e5; border-radius: 6px; overflow: hidden; margin-bottom: 36px; }
    .card  { padding: 16px 14px; border-right: 1px solid #e5e5e5; }
    .card:last-child { border-right: none; }
    .card .val  { font-size: 24px; font-weight: 600; line-height: 1; }
    .card .lbl  { font-size: 11px; color: #999; margin-top: 4px; text-transform: uppercase; letter-spacing: .05em; }

    /* ── pass rate bar ── */
    .rate-wrap  { margin-bottom: 36px; }
    .rate-row   { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
    .rate-label { font-size: 12px; color: #555; }
    .rate-pct   { font-size: 13px; font-weight: 600; }
    .bar-track  { height: 5px; background: #f0f0f0; border-radius: 99px; }
    .bar-fill   { height: 5px; border-radius: 99px; }

    /* ── two-column grid ── */
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 36px; }

    /* ── panel ── */
    .panel { border: 1px solid #e5e5e5; border-radius: 6px; overflow: hidden; }
    .panel-head { padding: 12px 16px; border-bottom: 1px solid #e5e5e5; font-size: 12px; font-weight: 600; color: #555; background: #fafafa; }
    .panel-body { padding: 0; }

    /* ── table within panel ── */
    .ptable { width: 100%; border-collapse: collapse; }
    .ptable th { padding: 8px 16px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: #aaa; font-weight: 600; border-bottom: 1px solid #f0f0f0; }
    .ptable td { padding: 10px 16px; border-bottom: 1px solid #f5f5f5; font-size: 13px; vertical-align: middle; }
    .ptable tr:last-child td { border-bottom: none; }
    .ptable tr:hover td { background: #fafafa; }

    /* inline mini bar */
    .mbar-wrap  { display: flex; align-items: center; gap: 8px; }
    .mbar-track { flex: 1; height: 3px; background: #f0f0f0; border-radius: 99px; }
    .mbar-fill  { height: 3px; border-radius: 99px; }
    .mbar-pct   { font-size: 11px; color: #888; width: 36px; text-align: right; }

    /* ── failures section ── */
    .failures-wrap { margin-bottom: 36px; }
    .fail-table { width: 100%; border-collapse: collapse; border: 1px solid #e5e5e5; border-radius: 6px; overflow: hidden; }
    .fail-table th { padding: 9px 14px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: #aaa; font-weight: 600; background: #fafafa; border-bottom: 1px solid #e5e5e5; }
    .fail-table td { padding: 9px 14px; font-size: 13px; border-bottom: 1px solid #f5f5f5; vertical-align: middle; color: #333; }
    .fail-table tr:last-child td { border-bottom: none; }
    .fail-table tr:hover td { background: #fff8f8; }

    /* ── full results table ── */
    .results-wrap { margin-bottom: 36px; }
    .rtable { width: 100%; border-collapse: collapse; border: 1px solid #e5e5e5; border-radius: 6px; overflow: hidden; }
    .rtable thead tr { background: #fafafa; border-bottom: 1px solid #e5e5e5; }
    .rtable th { padding: 9px 14px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: #aaa; font-weight: 600; }
    .rtable td { padding: 9px 14px; border-bottom: 1px solid #f5f5f5; font-size: 13px; color: #333; vertical-align: middle; }
    .rtable tr:last-child td { border-bottom: none; }
    .rtable tr:hover td { background: #fafafa; }

    /* chips */
    .chip { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; font-weight: 500; }
    .dot  { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
    .dot-pass  { background: #16a34a; }
    .dot-fail  { background: #dc2626; }
    .dot-error { background: #ca8a04; }
    .c-pass  { color: #16a34a; }
    .c-fail  { color: #dc2626; }
    .c-err   { color: #ca8a04; }
    .c-muted { color: #999; }

    code { font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px; color: #555; background: #f5f5f5; padding: 1px 5px; border-radius: 3px; }

    footer { font-size: 11px; color: #ccc; margin-top: 48px; border-top: 1px solid #f0f0f0; padding-top: 16px; }
  </style>
</head>
<body>
<div class="page">

  <!-- ── Header ── -->
  <div class="header">
    <div>
      <h1>{{ result.suite_name }}</h1>
      <div style="margin-top:6px; font-size:12px; color:#999;">{{ result.connection }}</div>
    </div>
    <div class="meta">
      <div>Generated <strong>{{ generated_at }}</strong></div>
      <div>
        <span class="tag">{{ result.total }} checks</span>
        <span class="tag">{{ table_data | length }} tables</span>
        <span class="tag">{{ unique_fields }} fields</span>
        <span class="tag">{{ duration }}s</span>
      </div>
    </div>
  </div>

  <!-- ── Summary Cards ── -->
  <div class="section-title">Overview</div>
  <div class="cards">
    <div class="card">
      <div class="val">{{ "{:,}".format(total_rows_scanned) }}</div>
      <div class="lbl">Total Rows</div>
    </div>
    <div class="card">
      <div class="val">{{ table_data | length }}</div>
      <div class="lbl">Tables</div>
    </div>
    <div class="card">
      <div class="val">{{ unique_fields }}</div>
      <div class="lbl">Fields</div>
    </div>
    <div class="card">
      <div class="val">{{ result.total }}</div>
      <div class="lbl">Checks Run</div>
    </div>
    <div class="card">
      <div class="val c-pass">{{ result.passed }}</div>
      <div class="lbl">Passed</div>
    </div>
    <div class="card">
      <div class="val c-fail">{{ result.failed }}</div>
      <div class="lbl">Failed</div>
    </div>
    <div class="card">
      <div class="val c-err">{{ result.errors }}</div>
      <div class="lbl">Errors</div>
    </div>
    <div class="card">
      <div class="val" style="color:{{ pass_rate_color }}">{{ "%.1f"|format(result.pass_rate) }}%</div>
      <div class="lbl">Pass Rate</div>
    </div>
  </div>

  <!-- ── Pass Rate Bar ── -->
  <div class="rate-wrap">
    <div class="rate-row">
      <span class="rate-label">Overall pass rate</span>
      <span class="rate-pct" style="color:{{ pass_rate_color }}">{{ "%.1f"|format(result.pass_rate) }}%</span>
    </div>
    <div class="bar-track">
      <div class="bar-fill" style="width:{{ "%.1f"|format(result.pass_rate) }}%; background:{{ pass_rate_color }};"></div>
    </div>
  </div>

  <!-- ── Table + Category breakdown ── -->
  <div class="grid-2">

    <!-- Table breakdown -->
    <div>
      <div class="section-title">By Table</div>
      <div class="panel">
        <table class="ptable">
          <thead>
            <tr>
              <th>Table</th>
              <th style="text-align:right">Rows</th>
              <th style="text-align:right">Fields</th>
              <th style="text-align:right">Checks</th>
              <th style="min-width:130px">Pass Rate</th>
            </tr>
          </thead>
          <tbody>
            {% for t in table_data %}
            <tr>
              <td><strong>{{ t.name }}</strong></td>
              <td style="text-align:right; color:#888">{{ "{:,}".format(t.rows) }}</td>
              <td style="text-align:right; color:#888">{{ t.fields }}</td>
              <td style="text-align:right; color:#888">
                <span class="c-pass">{{ t.passed }}</span>/<span class="c-fail">{{ t.failed }}</span>
                {% if t.errors %}<span class="c-err">/{{ t.errors }}</span>{% endif %}
              </td>
              <td>
                <div class="mbar-wrap">
                  <div class="mbar-track">
                    <div class="mbar-fill" style="width:{{ t.rate }}%; background:{{ t.rate_color }};"></div>
                  </div>
                  <span class="mbar-pct" style="color:{{ t.rate_color }}">{{ t.rate }}%</span>
                </div>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Category breakdown -->
    <div>
      <div class="section-title">By Check Category</div>
      <div class="panel">
        <table class="ptable">
          <thead>
            <tr>
              <th>Category</th>
              <th style="text-align:right">Checks</th>
              <th style="text-align:right">Failed</th>
              <th style="min-width:130px">Pass Rate</th>
            </tr>
          </thead>
          <tbody>
            {% for c in category_data %}
            <tr>
              <td><strong>{{ c.name }}</strong></td>
              <td style="text-align:right; color:#888">{{ c.total }}</td>
              <td style="text-align:right">
                {% if c.failed > 0 %}<span class="c-fail">{{ c.failed }}</span>{% else %}<span class="c-muted">0</span>{% endif %}
              </td>
              <td>
                <div class="mbar-wrap">
                  <div class="mbar-track">
                    <div class="mbar-fill" style="width:{{ c.rate }}%; background:{{ c.rate_color }};"></div>
                  </div>
                  <span class="mbar-pct" style="color:{{ c.rate_color }}">{{ c.rate }}%</span>
                </div>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

  </div>

  <!-- ── Failures ── -->
  {% if failures %}
  <div class="failures-wrap">
    <div class="section-title">Failed Checks &mdash; {{ failures | length }} issue{{ 's' if failures | length != 1 else '' }}</div>
    <div class="panel">
      <table class="ptable">
        <thead>
          <tr>
            <th>Table</th>
            <th>Field</th>
            <th>Check</th>
            <th>Finding</th>
          </tr>
        </thead>
        <tbody>
          {% for r in failures %}
          <tr>
            <td style="color:#888">{{ r.table }}</td>
            <td><strong>{{ r.field }}</strong></td>
            <td><code>{{ r.check_type }}</code></td>
            <td style="color:#dc2626">{{ r.message }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
  {% endif %}

  <!-- ── Full Results ── -->
  <div class="results-wrap">
    <div class="section-title">All Check Results</div>
    <div class="panel">
      <table class="ptable">
        <thead>
          <tr>
            <th>Table</th>
            <th>Field</th>
            <th>Check</th>
            <th>Status</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {% for r in result.results %}
          <tr>
            <td class="c-muted">{{ r.table }}</td>
            <td><strong>{{ r.field }}</strong></td>
            <td><code>{{ r.check_type }}</code></td>
            <td>
              {% if r.status.value == "PASS" %}
                <span class="chip"><span class="dot dot-pass"></span><span class="c-pass">Pass</span></span>
              {% elif r.status.value == "FAIL" %}
                <span class="chip"><span class="dot dot-fail"></span><span class="c-fail">Fail</span></span>
              {% else %}
                <span class="chip"><span class="dot dot-error"></span><span class="c-err">Error</span></span>
              {% endif %}
            </td>
            <td style="color:#555; font-size:12px;">{{ r.message }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  <footer>TestNucleus &mdash; Data Quality Validation Framework</footer>

</div>
</body>
</html>"""


def export_json(result: SuiteResult, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = result.model_dump(mode="json")
    data["summary"] = {
        "total":              result.total,
        "passed":             result.passed,
        "failed":             result.failed,
        "errors":             result.errors,
        "pass_rate":          round(result.pass_rate, 2),
        "total_rows_scanned": sum(result.table_stats.values()),
        "tables_checked":     len(result.table_stats),
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def export_html(result: SuiteResult, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ctx = _build_context(result)
    html = Template(_HTML_TEMPLATE).render(**ctx)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
