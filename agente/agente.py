#!/usr/bin/env python3
"""agente — o host MCP da palestra, em um arquivo.

Liga o Ollama local (qwen3:8b) a DOIS servidores MCP, ambos somente leitura:

- mcp-grafana com -disable-write → métricas (Prometheus) e logs (Loki)
- o servidor MCP nativo do Tempo (/api/mcp) → traces via TraceQL

O loop é o clássico: o modelo pede uma ferramenta, o humano aprova no portão,
o resultado volta cortado, repete até o diagnóstico.

Rodada 1: só este arquivo, 5 ferramentas genéricas, system prompt sem nenhuma
dica do ambiente. Rodada 2 (--com-contexto): os arquivos de contexto/*.md
entram no system prompt — e é só isso que muda. A diferença de resultado é a
tese da palestra.

As 5 ferramentas: uma de descoberta (list_datasources), métrica, log, busca
de traces e trace por ID. O mcp-grafana ainda sobe só com as categorias
datasource/prometheus/loki, e o host filtra tudo pela lista FERRAMENTAS —
expor pouco é decisão de interface, e a interface é o contexto.
"""

import argparse
import asyncio
import os
import pathlib
import sys
import time

import requests
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

OLLAMA = "http://localhost:11434"
TEMPO_MCP = "http://localhost:3200/api/mcp"
MODELO = "qwen3:8b"
LIMITE_SAIDA = 2000     # chars devolvidos ao modelo por ferramenta
MAX_PASSOS = 8          # teto de iterações; no palco ninguém espera o passo 9

CINZA, VERDE, AMARELO, VERMELHO, NEGRITO, FIM = (
    "\033[90m", "\033[32m", "\033[33m", "\033[31m", "\033[1m", "\033[0m")

FERRAMENTAS = [
    "list_datasources",   # o que existe neste Grafana
    "query_prometheus",   # métricas
    "query_loki_logs",    # logs
    "traceql-search",     # busca de traces (Tempo MCP)
    "get-trace",          # um trace específico por ID (Tempo MCP)
]

SERVIDOR_MCP = StdioServerParameters(
    command="mcp-grafana",
    args=["-t", "stdio", "-disable-write",
          "-enabled-tools", "datasource,prometheus,loki"],
    env={"GRAFANA_URL": "http://localhost:3000",
         "GRAFANA_USERNAME": "admin", "GRAFANA_PASSWORD": "admin"},
)

PROMPT_BASE = (
    "Você é um agente de investigação de incidentes com acesso somente leitura "
    "à observabilidade: métricas (Prometheus), logs (Loki) e traces (Tempo, "
    "via TraceQL). Investigue usando as ferramentas antes de concluir. "
    "Responda em português, e termine com um diagnóstico objetivo da causa "
    "raiz mais provável."
)


def montar_system_prompt(com_contexto: bool) -> str:
    if not com_contexto:
        return PROMPT_BASE
    pedacos = [PROMPT_BASE]
    for arq in sorted(pathlib.Path(__file__).parent.parent.glob("contexto/*.md")):
        if arq.name != "LEIAME.md":
            pedacos.append(f"\n--- {arq.name} ---\n{arq.read_text()}")
    return "\n".join(pedacos)


def truncar(texto: str) -> str:
    if len(texto) <= LIMITE_SAIDA:
        return texto
    return (texto[:LIMITE_SAIDA]
            + f"\n[... SAÍDA CORTADA: {len(texto) - LIMITE_SAIDA} chars omitidos ...]")


def portao_humano(nome: str, args: dict, auto: bool) -> bool:
    """O portão. Imprime o que o modelo quer fazer e espera o humano."""
    print(f"\n{AMARELO}┌─ PORTÃO HUMANO ─────────────────────────────{FIM}")
    print(f"{AMARELO}│{FIM} ferramenta: {NEGRITO}{nome}{FIM}")
    for chave, valor in args.items():
        print(f"{AMARELO}│{FIM}   {chave} = {valor}")
    if auto:
        print(f"{AMARELO}└─{FIM} aprovado automaticamente (--sim)")
        return True
    resposta = input(f"{AMARELO}└─{FIM} Enter aprova, 'n' nega: ").strip().lower()
    return resposta != "n"


def chamar_ollama(mensagens: list, tools: list) -> dict:
    inicio = time.monotonic()
    resposta = requests.post(f"{OLLAMA}/api/chat", timeout=300, json={
        "model": MODELO, "messages": mensagens, "tools": tools,
        "stream": False,
        # think=False: o modo de raciocínio do qwen3 dobra a latência por
        # passo; em 30 min de palco esse é o orçamento mais escasso.
        "think": False,
        "options": {"temperature": 0.2},  # investigação pede pouco improviso
    })
    resposta.raise_for_status()
    corpo = resposta.json()
    corpo["_segundos"] = time.monotonic() - inicio
    return corpo


async def investigar(pergunta: str, com_contexto: bool, auto: bool) -> None:
    # stderr do servidor vai para /dev/null: os logs de arranque do
    # mcp-grafana poluiriam o telão no exato momento de abertura da demo.
    with open(os.devnull, "w") as ralo:
        await _investigar(pergunta, com_contexto, auto, ralo)


async def _investigar(pergunta, com_contexto, auto, ralo) -> None:
    async with stdio_client(SERVIDOR_MCP, errlog=ralo) as (leitura, escrita), \
            streamable_http_client(TEMPO_MCP) as fluxo_tempo:
        async with ClientSession(leitura, escrita) as grafana, \
                ClientSession(fluxo_tempo[0], fluxo_tempo[1]) as tempo:
            await grafana.initialize()
            await tempo.initialize()
            todas, dona = [], {}
            for sessao_mcp in (grafana, tempo):
                for t in (await sessao_mcp.list_tools()).tools:
                    todas.append(t)
                    dona[t.name] = sessao_mcp
            expostas = [t for t in todas if t.name in FERRAMENTAS]
            tools_ollama = [{"type": "function", "function": {
                "name": t.name, "description": t.description,
                "parameters": t.input_schema}} for t in expostas]

            rotulo = "COM contexto de ambiente" if com_contexto else "SEM contexto de ambiente"
            print(f"{NEGRITO}Agente de investigação — {rotulo}{FIM}")
            print(f"{CINZA}modelo {MODELO} · {len(expostas)} ferramentas expostas "
                  f"(de {len(todas)} nos 2 servidores MCP, escrita desabilitada){FIM}")
            for t in expostas:
                print(f"{CINZA}  · {t.name}{FIM}")

            mensagens = [
                {"role": "system", "content": montar_system_prompt(com_contexto)},
                {"role": "user", "content": pergunta},
            ]
            tempo_total_modelo = 0.0

            for passo in range(1, MAX_PASSOS + 1):
                corpo = chamar_ollama(mensagens, tools_ollama)
                tempo_total_modelo += corpo["_segundos"]
                msg = corpo["message"]
                mensagens.append({k: v for k, v in msg.items() if k != "thinking"})
                chamadas = msg.get("tool_calls") or []

                if not chamadas:
                    print(f"\n{VERDE}{NEGRITO}═══ DIAGNÓSTICO (passo {passo}) ═══{FIM}")
                    print(msg.get("content", "").strip())
                    print(f"\n{CINZA}tempo de modelo: {tempo_total_modelo:.1f}s "
                          f"em {passo} passo(s){FIM}")
                    return

                for chamada in chamadas:
                    nome = chamada["function"]["name"]
                    args = chamada["function"].get("arguments") or {}
                    print(f"\n{CINZA}passo {passo} · modelo pensou por "
                          f"{corpo['_segundos']:.1f}s{FIM}")

                    if nome not in FERRAMENTAS:
                        resultado = f"ferramenta desconhecida: {nome}"
                    elif not portao_humano(nome, args, auto):
                        resultado = "NEGADO pelo operador humano."
                        print(f"{VERMELHO}✗ negado{FIM}")
                    else:
                        try:
                            retorno = await dona[nome].call_tool(nome, args)
                            resultado = "\n".join(
                                c.text for c in retorno.content
                                if getattr(c, "text", None)) or "(vazio)"
                        except Exception as erro:  # noqa: BLE001
                            resultado = f"erro na ferramenta: {erro}"
                        print(f"{VERDE}✓ executado{FIM} "
                              f"{CINZA}({len(resultado)} chars"
                              f"{', cortado' if len(resultado) > LIMITE_SAIDA else ''}){FIM}")
                    mensagens.append({"role": "tool", "tool_name": nome,
                                      "content": truncar(resultado)})

            print(f"\n{VERMELHO}Teto de {MAX_PASSOS} passos atingido sem diagnóstico.{FIM}")
            print(f"{CINZA}tempo de modelo: {tempo_total_modelo:.1f}s{FIM}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agente de investigação da palestra")
    parser.add_argument("--pergunta", default=(
        "O checkout-api está devolvendo erro 503 para os clientes agora. "
        "Investigue e me diga a causa raiz."))
    parser.add_argument("--com-contexto", action="store_true",
                        help="rodada 2: injeta contexto/*.md no system prompt")
    parser.add_argument("--sim", action="store_true",
                        help="aprova todas as ferramentas (calibração/ensaio)")
    argumentos = parser.parse_args()
    try:
        asyncio.run(investigar(argumentos.pergunta,
                               argumentos.com_contexto, argumentos.sim))
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
