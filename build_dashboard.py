#!/usr/bin/env python3
"""
Le data/tickets.csv, calcula os indicadores do help desk e gera um dashboard
HTML autossuficiente (graficos em SVG inline — abre em qualquer navegador,
sem internet e sem dependencias de JavaScript).

Saida: dashboard.html  +  docs/dashboard.png (via screenshot separado)
"""
import os
from datetime import datetime
from html import escape

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Paleta categorica validada (dataviz) — cor segue a entidade, fixa ---
CAT_COLORS = {
    "Hardware": "#2a78d6", "Rede": "#eb6834", "Acesso": "#1baf7a",
    "Software/Office": "#eda100", "Impressão": "#e87ba4", "Outros": "#008300",
}
PRIO_COLORS = {"Crítica": "#e34948", "Alta": "#eb6834", "Média": "#eda100", "Baixa": "#1baf7a"}
INK, MUTED, GRID, GOOD, BAD = "#1a2233", "#5b6678", "#e6e9f0", "#22a06b", "#e5484d"
MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def fmt(n, dec=0):
    s = f"{n:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return s


# ---------------------------------------------------------------------------
# Graficos em SVG
# ---------------------------------------------------------------------------
def bar_chart(labels, values, colors, w=520, h=260, unit=""):
    pad_l, pad_b, pad_t, pad_r = 40, 46, 16, 12
    iw, ih = w - pad_l - pad_r, h - pad_b - pad_t
    vmax = max(values) if values else 1
    vmax = vmax * 1.15 or 1
    n = len(values)
    gap = 14
    bw = (iw - gap * (n - 1)) / n
    svg = [f'<svg viewBox="0 0 {w} {h}" role="img" width="100%" style="max-width:{w}px">']
    # gridlines + y ticks
    for k in range(5):
        gy = pad_t + ih - ih * k / 4
        val = vmax * k / 4
        svg.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{w-pad_r}" y2="{gy:.1f}" stroke="{GRID}" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l-6}" y="{gy+3:.1f}" text-anchor="end" font-size="10" fill="{MUTED}">{fmt(val)}</text>')
    for i, (lab, val, col) in enumerate(zip(labels, values, colors)):
        x = pad_l + i * (bw + gap)
        bh = ih * val / vmax
        y = pad_t + ih - bh
        svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{col}">'
                   f'<title>{escape(lab)}: {fmt(val)}{unit}</title></rect>')
        svg.append(f'<text x="{x+bw/2:.1f}" y="{y-5:.1f}" text-anchor="middle" font-size="11" font-weight="700" fill="{INK}">{fmt(val)}</text>')
        # rotula categoria (quebra em 1 linha curta)
        short = lab if len(lab) <= 12 else lab[:11] + "…"
        svg.append(f'<text x="{x+bw/2:.1f}" y="{h-pad_b+16:.1f}" text-anchor="middle" font-size="10" fill="{MUTED}">{escape(short)}</text>')
    svg.append('</svg>')
    return "".join(svg)


def line_chart(labels, values, w=520, h=260, color="#2a78d6"):
    pad_l, pad_b, pad_t, pad_r = 40, 34, 18, 14
    iw, ih = w - pad_l - pad_r, h - pad_b - pad_t
    vmax = (max(values) if values else 1) * 1.15 or 1
    n = len(values)
    xs = [pad_l + (iw * i / (n - 1) if n > 1 else 0) for i in range(n)]
    ys = [pad_t + ih - ih * v / vmax for v in values]
    svg = [f'<svg viewBox="0 0 {w} {h}" role="img" width="100%" style="max-width:{w}px">']
    for k in range(5):
        gy = pad_t + ih - ih * k / 4
        svg.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{w-pad_r}" y2="{gy:.1f}" stroke="{GRID}" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l-6}" y="{gy+3:.1f}" text-anchor="end" font-size="10" fill="{MUTED}">{fmt(vmax*k/4)}</text>')
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    # area suave
    svg.append(f'<polyline points="{pad_l},{pad_t+ih} {pts} {xs[-1]:.1f},{pad_t+ih}" fill="{color}" opacity="0.08"/>')
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>')
    for x, y, lab, v in zip(xs, ys, labels, values):
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#fff" stroke="{color}" stroke-width="2"><title>{escape(lab)}: {fmt(v)} chamados</title></circle>')
        svg.append(f'<text x="{x:.1f}" y="{h-pad_b+16:.1f}" text-anchor="middle" font-size="10" fill="{MUTED}">{escape(lab)}</text>')
    svg.append('</svg>')
    return "".join(svg)


def donut(items, w=330, h=230):
    # items: [(label, value, color)]
    import math
    cx, cy, r, rin = 90, h / 2, 78, 46
    total = sum(v for _, v, _ in items) or 1
    svg = [f'<svg viewBox="0 0 {w} {h}" role="img" width="100%" style="max-width:{w}px">']
    ang = -math.pi / 2
    for lab, val, col in items:
        frac = val / total
        a2 = ang + frac * 2 * math.pi
        large = 1 if frac > 0.5 else 0
        x1, y1 = cx + r * math.cos(ang), cy + r * math.sin(ang)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        xi1, yi1 = cx + rin * math.cos(a2), cy + rin * math.sin(a2)
        xi2, yi2 = cx + rin * math.cos(ang), cy + rin * math.sin(ang)
        d = (f"M{x1:.1f},{y1:.1f} A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f} "
             f"L{xi1:.1f},{yi1:.1f} A{rin},{rin} 0 {large} 0 {xi2:.1f},{yi2:.1f} Z")
        svg.append(f'<path d="{d}" fill="{col}"><title>{escape(lab)}: {fmt(val)} ({frac*100:.0f}%)</title></path>')
        ang = a2
    svg.append(f'<text x="{cx}" y="{cy-4}" text-anchor="middle" font-size="22" font-weight="800" fill="{INK}">{fmt(total)}</text>')
    svg.append(f'<text x="{cx}" y="{cy+14}" text-anchor="middle" font-size="10" fill="{MUTED}">chamados</text>')
    # legenda
    ly = 28
    for lab, val, col in items:
        pct = round(val / total * 100)
        svg.append(f'<rect x="185" y="{ly-9}" width="11" height="11" rx="2" fill="{col}"/>')
        svg.append(f'<text x="201" y="{ly}" font-size="11" fill="{INK}">{escape(lab)}</text>')
        svg.append(f'<text x="{w-6}" y="{ly}" text-anchor="end" font-size="11" font-weight="700" fill="{MUTED}">{pct}%</text>')
        ly += 26
    svg.append('</svg>')
    return "".join(svg)


def hbar(labels, values, w=520, h=260, color="#2a78d6"):
    pad_l, pad_r, pad_t, pad_b = 120, 44, 8, 8
    n = len(values)
    ih = h - pad_t - pad_b
    row = ih / n
    bh = row * 0.62
    vmax = (max(values) if values else 1) or 1
    iw = w - pad_l - pad_r
    svg = [f'<svg viewBox="0 0 {w} {h}" role="img" width="100%" style="max-width:{w}px">']
    for i, (lab, val) in enumerate(zip(labels, values)):
        y = pad_t + i * row + (row - bh) / 2
        bw = iw * val / vmax
        svg.append(f'<text x="{pad_l-8}" y="{y+bh/2+4:.1f}" text-anchor="end" font-size="11" fill="{INK}">{escape(lab)}</text>')
        svg.append(f'<rect x="{pad_l}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{color}"><title>{escape(lab)}: {fmt(val)}</title></rect>')
        svg.append(f'<text x="{pad_l+bw+6:.1f}" y="{y+bh/2+4:.1f}" font-size="11" font-weight="700" fill="{MUTED}">{fmt(val)}</text>')
    svg.append('</svg>')
    return "".join(svg)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    df = pd.read_csv(os.path.join(ROOT, "data", "tickets.csv"))
    df["aberto_em"] = pd.to_datetime(df["aberto_em"])
    resolvidos = df[df["status"] == "Resolvido"].copy()
    total = len(df)
    backlog = int((df["status"] != "Resolvido").sum())
    mttr = resolvidos["tempo_resolucao_h"].astype(float).mean()
    sla_ok = (resolvidos["sla_cumprido"] == "sim").sum()
    sla_pct = 100 * sla_ok / len(resolvidos)

    # volume por categoria (ordem fixa da paleta)
    cats = list(CAT_COLORS.keys())
    vol_cat = [int((df["categoria"] == c).sum()) for c in cats]

    # por mes
    df["mes"] = df["aberto_em"].dt.to_period("M")
    por_mes = df.groupby("mes").size().sort_index()
    mes_labels = [f"{MESES_PT[p.month-1]}/{str(p.year)[2:]}" for p in por_mes.index]
    mes_vals = [int(v) for v in por_mes.values]

    # prioridade
    prios = ["Crítica", "Alta", "Média", "Baixa"]
    prio_items = [(p, int((df["prioridade"] == p).sum()), PRIO_COLORS[p]) for p in prios]

    # top unidades
    top_u = df["unidade"].value_counts().head(8)
    u_labels = list(top_u.index)
    u_vals = [int(v) for v in top_u.values]

    # tabela por categoria
    tab = []
    for c in cats:
        sub = resolvidos[resolvidos["categoria"] == c]
        vol = int((df["categoria"] == c).sum())
        m = sub["tempo_resolucao_h"].astype(float).mean() if len(sub) else 0
        s = 100 * (sub["sla_cumprido"] == "sim").sum() / len(sub) if len(sub) else 0
        tab.append((c, vol, m, s))

    periodo = f"{df['aberto_em'].min():%d/%m/%Y} a {df['aberto_em'].max():%d/%m/%Y}"
    render(total, backlog, mttr, sla_pct, cats, vol_cat, mes_labels, mes_vals,
           prio_items, u_labels, u_vals, tab, periodo)
    print(f"OK — dashboard.html gerado. total={total} SLA={sla_pct:.0f}% MTTR={mttr:.1f}h backlog={backlog}")


def render(total, backlog, mttr, sla_pct, cats, vol_cat, mes_labels, mes_vals,
           prio_items, u_labels, u_vals, tab, periodo):
    cat_colors = [CAT_COLORS[c] for c in cats]
    tab_rows = ""
    for c, vol, m, s in tab:
        scolor = GOOD if s >= 90 else (BAD if s < 80 else "#b6790f")
        tab_rows += (f"<tr><td><span class='dot' style='background:{CAT_COLORS[c]}'></span>{escape(c)}</td>"
                     f"<td class='num'>{fmt(vol)}</td><td class='num'>{fmt(m,1)} h</td>"
                     f"<td class='num' style='color:{scolor};font-weight:700'>{fmt(s)}%</td></tr>")
    sla_color = GOOD if sla_pct >= 90 else ("#b6790f" if sla_pct >= 80 else BAD)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard de Help Desk</title>
<style>
  :root{{--bg:#f4f6fb;--card:#fff;--ink:{INK};--muted:{MUTED};--line:{GRID};--green:{GOOD}}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI",system-ui,-apple-system,Arial,sans-serif;line-height:1.5}}
  .wrap{{max-width:1120px;margin:0 auto;padding:28px 20px 56px}}
  h1{{font-size:1.5rem;margin:0}} .sub{{color:var(--muted);font-size:.9rem;margin-top:4px}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:20px 0}}
  .kpi{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px}}
  .kpi .value{{font-size:1.9rem;font-weight:800}} .kpi .label{{color:var(--muted);font-size:.74rem;text-transform:uppercase;letter-spacing:.03em}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}}
  .card h2{{font-size:1rem;margin:0 0 10px}} .card .hint{{color:var(--muted);font-size:.78rem;margin:6px 0 0}}
  .full{{grid-column:1 / -1}}
  table{{width:100%;border-collapse:collapse;font-size:.92rem}}
  th,td{{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}}
  th{{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.03em}}
  td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}
  .dot{{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:8px;vertical-align:middle}}
  footer{{color:var(--muted);font-size:.8rem;text-align:center;margin-top:24px}}
  @media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
  <h1>Dashboard de Help Desk</h1>
  <div class="sub">Dados sintéticos (fictícios) &middot; período {periodo}</div>

  <div class="kpis">
    <div class="kpi"><div class="value">{fmt(total)}</div><div class="label">Total de chamados</div></div>
    <div class="kpi"><div class="value" style="color:{sla_color}">{fmt(sla_pct)}%</div><div class="label">SLA cumprido</div></div>
    <div class="kpi"><div class="value">{fmt(mttr,1)} h</div><div class="label">Tempo médio de resolução</div></div>
    <div class="kpi"><div class="value">{fmt(backlog)}</div><div class="label">Em aberto (backlog)</div></div>
  </div>

  <div class="grid">
    <div class="card"><h2>Chamados por categoria</h2>{bar_chart(cats, vol_cat, cat_colors)}</div>
    <div class="card"><h2>Chamados por mês</h2>{line_chart(mes_labels, mes_vals)}</div>
    <div class="card"><h2>Distribuição por prioridade</h2>{donut(prio_items)}</div>
    <div class="card"><h2>Top unidades por volume</h2>{hbar(u_labels, u_vals)}</div>
    <div class="card full"><h2>Desempenho por categoria</h2>
      <table>
        <thead><tr><th>Categoria</th><th class="num">Volume</th><th class="num">Tempo médio</th><th class="num">SLA cumprido</th></tr></thead>
        <tbody>{tab_rows}</tbody>
      </table>
      <p class="hint">SLA cumprido = chamados resolvidos dentro da meta de horas da prioridade.</p>
    </div>
  </div>

  <footer>Gerado por <b>build_dashboard.py</b> &middot; Dashboard de Help Desk &middot; Gustavo Paiva</footer>
</div></body></html>"""
    with open(os.path.join(ROOT, "dashboard.html"), "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    main()
