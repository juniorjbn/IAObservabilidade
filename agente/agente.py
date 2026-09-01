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


# ─── Ferramentas de domínio (só entram na rodada 2, com --com-contexto) ─────
# Não são wrappers de PromQL: cada uma responde uma pergunta que um humano
# de plantão DESTE ambiente faria. A interface é o contexto.

GRAFANA_PROXY = "http://localhost:3000/api/datasources/proxy/uid"
AUTH_GRAFANA = ("admin", "admin")
POSTGRES_DSN = "postgresql://demo:demo@localhost:5432/loja"


def _prom(consulta: str) -> list:
    resposta = requests.get(f"{GRAFANA_PROXY}/prometheus/api/v1/query",
                            params={"query": consulta},
                            auth=AUTH_GRAFANA, timeout=10)
    resposta.raise_for_status()
    return resposta.json()["data"]["result"]


def saude_do_pool(**_args) -> str:
    """Estado do pool de conexões de cada serviço, num relance."""
    em_uso = {m["metric"].get("service_name", "?"): float(m["value"][1])
              for m in _prom("db_pool_conexoes_em_uso")}
    capacidade = {m["metric"].get("service_name", "?"): float(m["value"][1])
                  for m in _prom("db_pool_capacidade")}
    esgotos = {m["metric"].get("service_name", "?"): float(m["value"][1])
               for m in _prom("sum by (service_name) "
                              "(increase(db_pool_esgotamentos_total[15m]))")}
    linhas = ["serviço | em uso/capacidade | esgotamentos (15min)"]
    for svc in sorted(capacidade):
        cheio = " <- POOL NO LIMITE" if em_uso.get(svc, 0) >= capacidade[svc] else ""
        linhas.append(f"{svc} | {em_uso.get(svc, 0):.0f}/{capacidade[svc]:.0f} | "
                      f"{esgotos.get(svc, 0):.0f}{cheio}")
    return "\n".join(linhas)


def quem_esta_segurando_locks(**_args) -> str:
    """Sessões bloqueadas no Postgres e quem as bloqueia, por nome."""
    import psycopg2
    sql = """
        SELECT bloqueada.application_name,
               bloqueadora.application_name,
               COALESCE(round(extract(epoch FROM now() - bloqueadora.xact_start)), 0),
               left(bloqueadora.query, 90)
        FROM pg_stat_activity bloqueada
        JOIN LATERAL unnest(pg_blocking_pids(bloqueada.pid)) AS b(pid) ON true
        JOIN pg_stat_activity bloqueadora ON bloqueadora.pid = b.pid
    """
    with psycopg2.connect(POSTGRES_DSN, connect_timeout=5) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql)
            linhas = cursor.fetchall()
    if not linhas:
        return "Nenhuma sessão bloqueada no banco agora."
    saida = ["quem espera | quem bloqueia | transação aberta há (s) | última query de quem bloqueia"]
    saida += [f"{a or '?'} | {b or '?'} | {c:.0f}s | {q}" for a, b, c, q in linhas]
    return "\n".join(saida)


def mudancas_recentes(janela_minutos: int = 60, **_args) -> str:
    """Mudanças de configuração registradas nos logs na janela recente."""
    agora_ns = int(time.time() * 1e9)
    inicio_ns = agora_ns - int(janela_minutos) * 60 * 1_000_000_000
    resposta = requests.get(
        f"{GRAFANA_PROXY}/loki/loki/api/v1/query_range",
        params={"query": '{service_name=~".+"} |= "mudança de configuração"',
                "start": inicio_ns, "end": agora_ns, "limit": 20},
        auth=AUTH_GRAFANA, timeout=10)
    resposta.raise_for_status()
    eventos = []
    for fluxo in resposta.json()["data"]["result"]:
        servico = fluxo["stream"].get("service_name", "?")
        for _ts, linha in fluxo["values"]:
            eventos.append(f"[{servico}] {linha.strip()}")
    return "\n".join(eventos) or f"Nenhuma mudança registrada nos últimos {janela_minutos} min."


FERRAMENTAS_DOMINIO = {
    "saude_do_pool": (saude_do_pool, {
        "type": "object", "properties": {}, "required": []},
        "Estado atual do pool de conexões de banco de cada serviço: em uso, "
        "capacidade e esgotamentos recentes."),
    "quem_esta_segurando_locks": (quem_esta_segurando_locks, {
        "type": "object", "properties": {}, "required": []},
        "Sessões bloqueadas no Postgres agora e quem as bloqueia, com o nome "
        "da aplicação e a idade da transação."),
    "mudancas_recentes": (mudancas_recentes, {
        "type": "object", "properties": {"janela_minutos": {"type": "integer",
        "description": "janela em minutos (padrão 60)"}}, "required": []},
        "Deploys, flags e configs alteradas registradas nos logs na janela "
        "recente."),
}


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
            nomes_validos = set(FERRAMENTAS)
            if com_contexto:
                nomes_validos |= set(FERRAMENTAS_DOMINIO)
                tools_ollama += [{"type": "function", "function": {
                    "name": nome, "description": descricao,
                    "parameters": schema}}
                    for nome, (_f, schema, descricao) in FERRAMENTAS_DOMINIO.items()]

            rotulo = "COM contexto de ambiente" if com_contexto else "SEM contexto de ambiente"
            print(f"{NEGRITO}Agente de investigação — {rotulo}{FIM}")
            print(f"{CINZA}modelo {MODELO} · {len(tools_ollama)} ferramentas expostas "
                  f"(de {len(todas)} nos 2 servidores MCP, escrita desabilitada){FIM}")
            for ferramenta in tools_ollama:
                print(f"{CINZA}  · {ferramenta['function']['name']}{FIM}")

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

                    if nome not in nomes_validos:
                        resultado = f"ferramenta desconhecida: {nome}"
                    elif not portao_humano(nome, args, auto):
                        resultado = "NEGADO pelo operador humano."
                        print(f"{VERMELHO}✗ negado{FIM}")
                    elif nome in FERRAMENTAS_DOMINIO:
                        try:
                            resultado = FERRAMENTAS_DOMINIO[nome][0](**args)
                        except Exception as erro:  # noqa: BLE001
                            resultado = f"erro na ferramenta: {erro}"
                        print(f"{VERDE}✓ executado{FIM} "
                              f"{CINZA}({len(resultado)} chars, domínio){FIM}")
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

            # Teto atingido: última palavra forçada, sem ferramentas. A
            # calibração mostrou o modelo com a evidência completa no
            # histórico gastando os passos finais em "confirmações".
            print(f"\n{AMARELO}Teto de {MAX_PASSOS} passos — o host encerra e "
                  f"pede a conclusão.{FIM}")
            mensagens.append({"role": "user", "content": (
                "Encerre AGORA com seu diagnóstico objetivo da causa raiz, "
                "baseado apenas no que você já coletou.")})
            corpo = chamar_ollama(mensagens, [], pensar)
            tempo_total_modelo += corpo["_segundos"]
            print(f"\n{VERDE}{NEGRITO}═══ DIAGNÓSTICO (forçado no teto) ═══{FIM}")
            print((corpo["message"].get("content") or "").strip())
            print(f"\n{CINZA}tempo de modelo: {tempo_total_modelo:.1f}s "
                  f"em {MAX_PASSOS}+1 passos{FIM}")


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
