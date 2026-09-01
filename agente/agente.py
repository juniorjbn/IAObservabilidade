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

As 5 ferramentas: descoberta de datasources, métrica, log, busca de traces
e descoberta de labels do Loki. O mcp-grafana ainda sobe só com as categorias
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
# Sobrescrevível por ambiente: a calibração compara modelos sem tocar código.
MODELO = os.getenv("MODELO_OLLAMA", "qwen3:8b")
LIMITE_SAIDA = 2000     # chars devolvidos ao modelo por ferramenta
MAX_PASSOS = 8          # teto de iterações; no palco ninguém espera o passo 9

CINZA, VERDE, AMARELO, VERMELHO, NEGRITO, FIM = (
    "\033[90m", "\033[32m", "\033[33m", "\033[31m", "\033[1m", "\033[0m")

FERRAMENTAS = [
    "list_datasources",   # o que existe neste Grafana
    "query_prometheus",   # métricas
    "query_loki_logs",    # logs
    "traceql-search",         # busca de traces (Tempo MCP)
    "list_loki_label_names",  # descobrir quais labels existem antes de filtrar
]

SERVIDOR_MCP = StdioServerParameters(
    command="mcp-grafana",
    args=["-t", "stdio", "-disable-write",
          "-enabled-tools", "datasource,prometheus,loki"],
    env={"GRAFANA_URL": "http://localhost:3000",
         "GRAFANA_USERNAME": "admin", "GRAFANA_PASSWORD": "admin"},
)

# O prompt v2 ensina o CONTRATO das ferramentas — conhecimento de ofício de
# observabilidade, não do nosso ambiente. A calibração v1 (0/10) mostrou o
# modelo filtrando datasources por serviço, inventando labels e terminando
# com resposta vazia; cada linha abaixo ataca um desses tropeços medidos.
PROMPT_BASE = (
    "Você é um agente de investigação de incidentes com acesso somente leitura "
    "à observabilidade: métricas (Prometheus), logs (Loki) e traces (Tempo, "
    "via TraceQL). Investigue usando as ferramentas antes de concluir. "
    "Responda em português, e termine com um diagnóstico objetivo da causa "
    "raiz mais provável.\n"
    "Regras de ofício:\n"
    "- Datasources são compartilhados por todos os serviços. Chame "
    "list_datasources no máximo UMA vez, sem filtros; o filtro por serviço "
    "acontece dentro das queries, nunca na lista de datasources.\n"
    "- TraceQL exige chaves e aspas: {resource.service.name = \"exemplo\"}. "
    "LogQL idem: {label=\"valor\"}.\n"
    "- Em traceql-search, omita start/end: o padrão já cobre a janela "
    "recente. Não use formatos relativos como now-1h.\n"
    "- Se uma consulta voltar vazia ou com erro de sintaxe, NÃO repita a mesma "
    "chamada: mude o label ou a abordagem (outra ferramenta, outro sinal).\n"
    "- Se você anunciar um próximo passo, execute-o chamando a ferramenta — "
    "não descreva a intenção em texto.\n"
    "- NUNCA responda com mensagem vazia. Quando tiver evidência suficiente, "
    "encerre com o diagnóstico; se as ferramentas não ajudarem, diga o que "
    "você concluiu com o que tem."
)


def montar_system_prompt(com_contexto: bool) -> str:
    if not com_contexto:
        return PROMPT_BASE
    pedacos = [PROMPT_BASE]
    for arq in sorted(pathlib.Path(__file__).parent.parent.glob("contexto/*.md")):
        if arq.name != "LEIAME.md":
            pedacos.append(f"\n--- {arq.name} ---\n{arq.read_text()}")
    return "\n".join(pedacos)


import datetime as _dt
import re as _re


def _rfc3339(valor: str) -> str:
    """Converte tempo relativo estilo Grafana ("now", "now-1h30m") em RFC3339.

    O MCP do Tempo só aceita RFC3339. Valor que não casar com o padrão passa
    intacto — se o modelo mandar RFC3339 de verdade, nada muda.
    """
    m = _re.fullmatch(r"now(?:-(\d+h)?(\d+m)?(\d+s)?)?", valor.strip())
    if not m:
        return valor
    h, mi, se = (int(g[:-1]) if g else 0 for g in m.groups())
    alvo = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=h, minutes=mi, seconds=se)
    return alvo.strftime("%Y-%m-%dT%H:%M:%SZ")


def _sanitizar_traceql(query: str) -> str:
    """Corta condições soltas depois das chaves: {...} and x = y -> {...}.

    Calibração D: 30 de 32 buscas de trace vieram com um "and status_code"
    apêndice — TraceQL não aceita nada fora das chaves, e o modelo lê o erro
    e insiste. A parte entre chaves é válida e devolve os traces que a
    investigação precisa; o host entrega o dialeto que a ferramenta fala.
    """
    m = _re.match(r"^\s*(\{[^}]*\})\s+(?:and|or|&&|\|\|)\s+", query)
    return m.group(1) if m else query


def normalizar_args(nome: str, args: dict) -> dict:
    if nome in ("traceql-search", "get-trace"):
        for chave in ("start", "end"):
            if isinstance(args.get(chave), str):
                args[chave] = _rfc3339(args[chave])
        if isinstance(args.get("query"), str):
            args["query"] = _sanitizar_traceql(args["query"])
    return args


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


def chamar_ollama(mensagens: list, tools: list, pensar: bool = False) -> dict:
    inicio = time.monotonic()
    resposta = requests.post(f"{OLLAMA}/api/chat", timeout=300, json={
        "model": MODELO, "messages": mensagens, "tools": tools,
        "stream": False,
        # think=False por padrão: o modo raciocínio dobra a latência por
        # passo. --pensar liga, para medir na calibração se o ganho de
        # acerto paga o custo de palco.
        "think": pensar,
        "options": {"temperature": 0.2},  # investigação pede pouco improviso
    })
    resposta.raise_for_status()
    corpo = resposta.json()
    corpo["_segundos"] = time.monotonic() - inicio
    return corpo


async def investigar(pergunta: str, com_contexto: bool, auto: bool,
                     pensar: bool = False) -> None:
    # stderr do servidor vai para /dev/null: os logs de arranque do
    # mcp-grafana poluiriam o telão no exato momento de abertura da demo.
    with open(os.devnull, "w") as ralo:
        await _investigar(pergunta, com_contexto, auto, ralo, pensar)


async def _investigar(pergunta, com_contexto, auto, ralo, pensar=False) -> None:
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
            reprompt_usado = False

            for passo in range(1, MAX_PASSOS + 1):
                corpo = chamar_ollama(mensagens, tools_ollama, pensar)
                tempo_total_modelo += corpo["_segundos"]
                msg = corpo["message"]
                mensagens.append({k: v for k, v in msg.items() if k != "thinking"})
                chamadas = msg.get("tool_calls") or []

                if not chamadas:
                    conteudo = (msg.get("content") or "").strip()
                    anuncia = any(fr in conteudo.lower() for fr in (
                        "vamos ", "próximo passo", "tentar novamente"))
                    if (not conteudo or anuncia) and not reprompt_usado \
                            and passo < MAX_PASSOS:
                        reprompt_usado = True
                        print(f"\n{AMARELO}↻ resposta sem diagnóstico — o host "
                              f"pede a conclusão (única vez){FIM}")
                        mensagens.append({"role": "user", "content": (
                            "Encerre AGORA com seu diagnóstico objetivo da "
                            "causa raiz, baseado apenas no que você já "
                            "coletou. Não chame mais ferramentas.")})
                        continue
                    print(f"\n{VERDE}{NEGRITO}═══ DIAGNÓSTICO (passo {passo}) ═══{FIM}")
                    print(conteudo)
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
                            retorno = await dona[nome].call_tool(
                                nome, normalizar_args(nome, args))
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
    parser.add_argument("--pensar", action="store_true",
                        help="liga o modo raciocínio do modelo (mais lento)")
    argumentos = parser.parse_args()
    try:
        asyncio.run(investigar(argumentos.pergunta, argumentos.com_contexto,
                               argumentos.sim, argumentos.pensar))
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
