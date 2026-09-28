#!/usr/bin/env python3
"""
Gera um dataset sintetico de chamados de help desk ao longo de ~6 meses,
com dados suficientes para um dashboard: categoria, prioridade, unidade,
datas de abertura/fechamento, tempo de resolucao e cumprimento de SLA.

Saida: data/tickets.csv    Nenhum dado real.
"""
import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

CATEGORIAS = ["Hardware", "Rede", "Acesso", "Software/Office", "Impressão", "Outros"]
# peso de ocorrencia por categoria (uns problemas aparecem mais)
PESO_CAT = [22, 16, 20, 24, 12, 6]

PRIORIDADES = ["Crítica", "Alta", "Média", "Baixa"]
PESO_PRIO = [6, 18, 46, 30]
# meta de SLA em horas por prioridade
SLA_HORAS = {"Crítica": 4, "Alta": 8, "Média": 24, "Baixa": 72}

UNIDADES = [
    "Loja Jundiaí", "Loja Centro", "Loja Shopping", "Loja Campinas", "Loja Sul",
    "Fábrica", "Financeiro", "RH", "Comercial", "Expedição", "Marketing", "Estilo",
]
PESO_UNID = [14, 12, 11, 9, 8, 13, 7, 5, 8, 6, 4, 3]


def horas_resolucao(prioridade):
    """Tempo de resolucao (h): a maioria dentro do SLA, parte estoura."""
    sla = SLA_HORAS[prioridade]
    # 80% resolve dentro de ~0.2x a 0.9x do SLA; 20% estoura
    if random.random() < 0.80:
        return round(random.uniform(0.15, 0.95) * sla, 1)
    return round(random.uniform(1.05, 2.6) * sla, 1)


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(root, "data"), exist_ok=True)

    fim = datetime(2026, 9, 21, 18, 0)
    inicio = fim - timedelta(days=182)   # ~6 meses
    n = 1500
    rows = []
    for i in range(1, n + 1):
        cat = random.choices(CATEGORIAS, weights=PESO_CAT)[0]
        prio = random.choices(PRIORIDADES, weights=PESO_PRIO)[0]
        unid = random.choices(UNIDADES, weights=PESO_UNID)[0]

        # abertura em horario comercial, dias uteis com leve tendencia de crescimento
        dias = random.triangular(0, 182, 130)   # mais chamados nos meses recentes
        aberto = inicio + timedelta(days=dias)
        aberto = aberto.replace(hour=random.randint(8, 17), minute=random.randint(0, 59), second=0)

        # 88% ja resolvidos; resto em aberto/andamento (backlog)
        resolvido = random.random() < 0.88
        if resolvido and aberto < fim - timedelta(hours=2):
            th = horas_resolucao(prio)
            fechado = aberto + timedelta(hours=th)
            if fechado > fim:
                fechado = fim
                th = round((fechado - aberto).total_seconds() / 3600, 1)
            sla_ok = th <= SLA_HORAS[prio]
            status = "Resolvido"
            fechado_str = fechado.strftime("%Y-%m-%d %H:%M")
            th_str = f"{th}"
            sla_str = "sim" if sla_ok else "nao"
        else:
            status = random.choice(["Aberto", "Em andamento"])
            fechado_str = ""
            th_str = ""
            sla_str = ""

        rows.append([
            f"CH-{i:05d}", aberto.strftime("%Y-%m-%d %H:%M"), fechado_str,
            cat, prio, unid, status, SLA_HORAS[prio], th_str, sla_str,
        ])

    rows.sort(key=lambda r: r[1])
    out = os.path.join(root, "data", "tickets.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "aberto_em", "fechado_em", "categoria", "prioridade",
                    "unidade", "status", "sla_horas", "tempo_resolucao_h", "sla_cumprido"])
        w.writerows(rows)
    print(f"OK: {len(rows)} chamados em data/tickets.csv")
    resolvidos = sum(1 for r in rows if r[6] == "Resolvido")
    print(f"  resolvidos: {resolvidos} | em aberto: {len(rows)-resolvidos}")


if __name__ == "__main__":
    main()
