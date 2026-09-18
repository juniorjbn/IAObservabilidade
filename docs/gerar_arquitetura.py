#!/usr/bin/env python3
"""Gera docs/arquitetura.excalidraw — a arquitetura da POC, editável no
excalidraw.com (File > Open) ou no plugin do VS Code.

    python3 docs/gerar_arquitetura.py
"""
import json, pathlib, random

random.seed(23)
els = []
_n = 0
def nid():
    global _n; _n += 1; return f"e{_n}"

BASE = dict(angle=0, strokeColor="#1e1e1e", fillStyle="solid", strokeWidth=2,
            strokeStyle="solid", roughness=1, opacity=100, groupIds=[], frameId=None,
            version=1, versionNonce=1, isDeleted=False, link=None, locked=False, updated=1)

def box(x, y, w, h, label, bg="#ffffff", size=16, dashed=False, bold=False):
    rid, tid = nid(), nid()
    els.append({**BASE, "id": rid, "type": "rectangle", "x": x, "y": y, "width": w, "height": h,
                "backgroundColor": bg, "roundness": {"type": 3}, "seed": random.randint(1, 10**6),
                "strokeStyle": "dashed" if dashed else "solid",
                "boundElements": [{"id": tid, "type": "text"}]})
    els.append({**BASE, "id": tid, "type": "text", "x": x + 8, "y": y + 8, "width": w - 16, "height": h - 16,
                "backgroundColor": "transparent", "seed": random.randint(1, 10**6), "boundElements": [],
                "text": label, "originalText": label, "fontSize": size, "fontFamily": 3 if not bold else 1,
                "textAlign": "center", "verticalAlign": "middle", "baseline": size, "lineHeight": 1.25,
                "containerId": rid, "autoResize": True})
    return rid, (x, y, w, h)

def label(x, y, text, size=14, color="#1e1e1e"):
    els.append({**BASE, "id": nid(), "type": "text", "x": x, "y": y, "width": 10 * len(text), "height": size * 1.25,
                "backgroundColor": "transparent", "strokeColor": color, "seed": random.randint(1, 10**6),
                "boundElements": [], "text": text, "originalText": text, "fontSize": size, "fontFamily": 1,
                "textAlign": "left", "verticalAlign": "top", "baseline": size, "lineHeight": 1.25,
                "containerId": None, "autoResize": True})

def arrow(x1, y1, x2, y2, text="", dashed=False, color="#1e1e1e"):
    aid = nid()
    els.append({**BASE, "id": aid, "type": "arrow", "x": x1, "y": y1, "width": abs(x2 - x1), "height": abs(y2 - y1),
                "backgroundColor": "transparent", "strokeColor": color, "seed": random.randint(1, 10**6),
                "strokeStyle": "dashed" if dashed else "solid", "roundness": {"type": 2},
                "points": [[0, 0], [x2 - x1, y2 - y1]], "lastCommittedPoint": None,
                "startBinding": None, "endBinding": None, "startArrowhead": None, "endArrowhead": "arrow",
                "boundElements": []})
    if text:
        label((x1 + x2) / 2 - 5 * len(text), (y1 + y2) / 2 - 22, text, 12, color)

def right(b): x, y, w, h = b; return (x + w, y + h / 2)
def left(b):  x, y, w, h = b; return (x, y + h / 2)
def top(b):   x, y, w, h = b; return (x + w / 2, y)
def bottom(b):x, y, w, h = b; return (x + w / 2, y + h)

# ── moldura: o notebook ────────────────────────────────────────────────
box(0, 0, 1500, 900, "", "#f8f9fa", dashed=True)
label(20, 14, "MacBook M3 Pro, 18 GB — tudo local, nada sai da máquina", 20)

# ── aplicação (esquerda) ───────────────────────────────────────────────
label(30, 70, "APLICAÇÃO  (Python 3.12 · FastAPI · OpenTelemetry SDK)", 14, "#868e96")
_, lg  = box(30, 110, 130, 60, "loadgen\n8 req/s", "#e9ecef")
_, ck  = box(220, 110, 160, 60, "checkout-api\npool 5", "#a5d8ff")
_, inv = box(440, 110, 160, 60, "inventory-api\npool 5 · 2s", "#a5d8ff")
_, pg  = box(440, 260, 160, 70, "Postgres 16\ntabela inventory", "#ffd8a8")
_, wk  = box(160, 260, 200, 70, "reconciliation-worker\nbackfill: FOR UPDATE 20s", "#ffc9c9")
arrow(*right(lg), *left(ck), "HTTP")
arrow(*right(ck), *left(inv), "HTTP /reservar")
arrow(*bottom(inv), *top(pg), "UPDATE (lock)")
arrow(*right(wk), *left(pg), "SQL", dashed=True, color="#c92a2a")
label(160, 340, "não aparece em nenhum trace da requisição", 12, "#c92a2a")

# ── observabilidade (centro) ───────────────────────────────────────────
_, lgtm = box(680, 70, 340, 330, "", "#fff9db")
label(695, 78, "grafana/otel-lgtm 0.32 — um container", 14, "#868e96")
_, col  = box(700, 110, 300, 44, "OTel Collector  ·  OTLP/HTTP :4318", "#ffec99")
_, prom = box(700, 175, 140, 50, "Prometheus 3.14\nmétricas", "#ffffff")
_, loki = box(860, 175, 140, 50, "Loki 3.7\nlogs", "#ffffff")
_, tmp  = box(700, 245, 140, 50, "Tempo 3.0\ntraces · MCP :3200", "#ffffff")
_, graf = box(860, 245, 140, 50, "Grafana 13\n:3000", "#ffffff")
_, dash = box(700, 320, 300, 44, "dashboard \"Loja — o incidente\"", "#ffffff")
arrow(*right(inv), *left(col), "traces · métricas · logs")
arrow(*bottom(col), *top(prom)); arrow(*bottom(col), *top(loki)); arrow(bottom(col)[0], bottom(col)[1], *top(tmp))

# ── agente (direita) ───────────────────────────────────────────────────
label(1060, 70, "AGENTE  (somente leitura · humano no portão)", 14, "#868e96")
_, oll = box(1080, 110, 380, 60, "Ollama 0.33 · qwen3:14b Q4_K_M · num_ctx 16k\nthink off · temp 0.2", "#d3f9d8")
_, ag  = box(1080, 210, 380, 90, "agente/agente.py\nloop ReAct · portão humano (Enter) · corte 2000 chars\nnarração fora da banda · 5 tools + 3 de domínio", "#b2f2bb")
_, mg  = box(1080, 340, 180, 60, "mcp-grafana 1.3\n-disable-write · stdio", "#c3fae8")
_, tmcp= box(1280, 340, 180, 60, "Tempo MCP\nstreamable HTTP", "#c3fae8")
_, dom = box(1080, 430, 380, 70, "ferramentas de domínio (rodada 2)\nsaude_do_pool · quem_esta_segurando_locks · mudancas_recentes", "#e5dbff")
_, ctx = box(1080, 530, 380, 70, "contexto/*.md  (~4 KB, rodada 2)\nmapa do ambiente · método de investigação", "#e5dbff")
arrow(*bottom(oll), *top(ag), "tool calls ↔")
arrow(bottom(ag)[0] - 100, bottom(ag)[1], top(mg)[0], top(mg)[1])
arrow(bottom(ag)[0] + 100, bottom(ag)[1], top(tmcp)[0], top(tmcp)[1])
arrow(*left(mg), *right(graf), "API (admin)")
arrow(*left(tmcp), right(tmp)[0], right(tmp)[1] + 10, "TraceQL", dashed=True)
arrow(*top(dom), bottom(ag)[0], bottom(ag)[1] + 40)
arrow(*top(ctx), *bottom(dom), "system prompt")
arrow(left(dom)[0], left(dom)[1] + 10, right(pg)[0], right(pg)[1] + 60, "pg_stat_activity (só leitura)", dashed=True, color="#5f3dc4")

# ── palco (embaixo) ────────────────────────────────────────────────────
label(30, 620, "PALCO", 14, "#868e96")
box(30, 650, 200, 50, "doitlive · roteiro/demo.sh", "#e9ecef")
box(250, 650, 200, 50, "glow + pandoc\ncontexto/*.md", "#e9ecef")
box(470, 650, 200, 50, "make preparar\nchecklist + memória", "#e9ecef")
box(690, 650, 200, 50, "make verificar\n100% → 0% → 100%", "#e9ecef")
box(910, 650, 240, 50, "calibração: baterias de 10\ncalibracao/rodar_bateria.py", "#e9ecef")

label(30, 760, "Rodada 1: 5 tools genéricas, sem contexto → culpa o inventory-api (0/90 acham o worker)", 14)
label(30, 790, "Rodada 2: + contexto/*.md + 3 tools de domínio → nomeia o worker, a flag e os locks (10/10, ~1 min)", 14)
label(30, 820, "Ablação: só o mapa 0/5 · mapa + método sem tools 0/5 · tudo 10/10 — a interface é o contexto", 14)

doc = {"type": "excalidraw", "version": 2, "source": "IAObservabilidade/docs/gerar_arquitetura.py",
       "elements": els, "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}, "files": {}}
out = pathlib.Path(__file__).with_name("arquitetura.excalidraw")
out.write_text(json.dumps(doc, ensure_ascii=False, indent=1))
print(out, len(els), "elementos")
