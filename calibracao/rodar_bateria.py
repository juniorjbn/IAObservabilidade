#!/usr/bin/env python3
"""Roda uma bateria de calibração conforme calibracao/PROTOCOLO.md.

Dispara N execuções do agente com --sim, incidente ativo do início ao fim,
uma conversa nova por execução. Classifica cada resultado pela tabela do
protocolo e grava logs + resumo em calibracao/resultados/.

    python3 calibracao/rodar_bateria.py                # rodada 1, 10 execuções
    python3 calibracao/rodar_bateria.py --com-contexto # rodada 2
    python3 calibracao/rodar_bateria.py --rodadas 3    # bateria curta de fumaça

A classificação automática é um palpite de triagem: o veredito final é de
quem lê os diagnósticos. O script deixa isso explícito no resumo.
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import os
import subprocess
import time
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PYTHON_AGENTE = RAIZ / "agente/.venv/bin/python"
AGENTE = RAIZ / "agente/agente.py"
WORKER = "http://localhost:8003"

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def controlar_incidente(acao: str) -> None:
    req = urllib.request.Request(
        f"{WORKER}/controle/backfill/{acao}", method="POST", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        if r.status != 200:
            raise SystemExit(f"falha ao {acao} o incidente (HTTP {r.status})")


def classificar(saida: str) -> tuple[str, str]:
    """Devolve (classe, diagnostico_resumido) segundo a tabela do protocolo."""
    m = re.search(r"═══ DIAGNÓSTICO \([^)]+\) ═══\n(.*?)\n\ntempo de modelo",
                  saida, re.DOTALL)
    if not m:
        return "falha_de_modelo", "(sem diagnóstico: teto de passos ou aborto)"
    diagnostico = m.group(1).strip()
    if not diagnostico:
        return "falha_de_modelo", "(diagnóstico vazio)"
    resumo = " ".join(diagnostico.split())[:220]
    texto = diagnostico.lower()
    if "reconciliation" in texto or "backfill" in texto:
        return "acerto_precoce", resumo
    if any(p in texto for p in ("inventory", "pool", "banco", "postgres",
                                 "lock", "conex")):
        return "erro_bom", resumo
    return "revisar_manualmente", resumo


def extrair_metricas(saida: str) -> dict:
    tempo = re.search(r"tempo de modelo: ([\d.]+)s em (\d+) passo", saida)
    ferramentas = re.findall(r"ferramenta: (\S+)", saida)
    return {
        "tempo_modelo_s": float(tempo.group(1)) if tempo else None,
        "passos": int(tempo.group(2)) if tempo else None,
        "ferramentas": ferramentas,
        "erros_de_ferramenta": len(re.findall(r"erro na ferramenta", saida)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rodadas", type=int, default=10)
    parser.add_argument("--com-contexto", action="store_true")
    parser.add_argument("--pensar", action="store_true")
    args = parser.parse_args()

    rodada = ("rodada2" if args.com_contexto else "rodada1")
    if args.pensar:
        rodada += "-pensar"
    modelo = os.getenv("MODELO_OLLAMA", "qwen3:8b")
    if modelo != "qwen3:8b":
        rodada += "-" + modelo.replace(":", "_")
    carimbo = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = RAIZ / "calibracao/resultados" / f"{carimbo}-{rodada}"
    destino.mkdir(parents=True)

    print(f"Bateria {rodada}: {args.rodadas} execuções → {destino}")
    controlar_incidente("ligar")
    print("incidente LIGADO; aguardando 5s para os locks pegarem")
    time.sleep(5)

    execucoes = []
    try:
        for i in range(1, args.rodadas + 1):
            cmd = [str(PYTHON_AGENTE), str(AGENTE), "--sim"]
            if args.com_contexto:
                cmd.append("--com-contexto")
            if args.pensar:
                cmd.append("--pensar")
            inicio = time.monotonic()
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=600, cwd=RAIZ)
            parede = time.monotonic() - inicio
            saida = ANSI.sub("", proc.stdout + proc.stderr)
            (destino / f"run_{i:02d}.log").write_text(saida)

            classe, resumo = classificar(saida)
            metricas = extrair_metricas(saida)
            execucoes.append({"run": i, "classe": classe, "diagnostico": resumo,
                              "parede_s": round(parede, 1), **metricas})
            print(f"  run {i:02d}: {classe:20s} "
                  f"({metricas['passos']} passos, "
                  f"{metricas['tempo_modelo_s']}s de modelo, "
                  f"{parede:.0f}s de parede)")
    finally:
        controlar_incidente("desligar")
        print("incidente DESLIGADO")

    contagem: dict[str, int] = {}
    for e in execucoes:
        contagem[e["classe"]] = contagem.get(e["classe"], 0) + 1

    meta = 9 if args.com_contexto else 8
    alvo = "acerto" if args.com_contexto else "erro_bom"
    resumo_final = {
        "rodada": rodada, "quando": carimbo, "execucoes": execucoes,
        "contagem": contagem, "meta": f">= {meta}/10 {alvo}",
    }
    (destino / "resumo.json").write_text(
        json.dumps(resumo_final, ensure_ascii=False, indent=2))

    print("\n── contagem ──")
    for classe, n in sorted(contagem.items()):
        print(f"  {classe}: {n}/{len(execucoes)}")
    print(f"\nMeta do protocolo: {resumo_final['meta']}")
    print("A classificação automática é triagem — LEIA os diagnósticos "
          f"em {destino}/run_*.log antes de declarar o veredito.")


if __name__ == "__main__":
    main()
