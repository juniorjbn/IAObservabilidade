#!/usr/bin/env python3
"""Monta calibracao/ABLACAO.md a partir dos logs das baterias.

Para cada condição, lista por execução: a sequência de ferramentas com os
argumentos, o tempo, e o diagnóstico final na íntegra. É o material para
responder "o que exatamente fecha o gap?" com log, não com opinião.

    python3 calibracao/gerar_ablacao.py
"""
from __future__ import annotations

import pathlib
import re

RAIZ = pathlib.Path(__file__).parent.parent
RES = RAIZ / "calibracao/resultados"

# (título, pasta, o que o agente tinha)
CONDICOES = [
    ("A · Rodada 1 — sem contexto",
     "20260915-181416-rodada1-qwen3_14b",
     "5 ferramentas genéricas do MCP. Nenhuma informação sobre o ambiente."),
    ("B · Ablação — só o mapa do ambiente",
     "20260917-143925-rodada2-qwen3_14b",
     "As mesmas 5 ferramentas + `mapa-do-ambiente.md` no system prompt "
     "(topologia com o worker desenhado, donos, tabela de fontes de verdade, "
     "'fatos que pegam gente nova'). SEM método, SEM ferramentas de domínio."),
    ("C · Ablação — mapa + método (o do palco)",
     "20260917-144726-rodada2-qwen3_14b",
     "As 5 ferramentas + mapa + `metodo-de-investigacao.md` — o método da "
     "rodada 2, que cita `saude_do_pool` e `quem_esta_segurando_locks` pelo "
     "nome. SEM ferramentas de domínio."),
    ("C' · Ablação — mapa + método genérico",
     "20260917-145207-rodada2-qwen3_14b",
     "As 5 ferramentas + mapa + `calibracao/ablacao/metodo-generico.md`: o "
     "mesmo método, reescrito sem citar ferramenta de domínio (passo 3 manda "
     "ler os logs de quem mais escreve no banco; passo 4, na falta de "
     "pg_stat_activity, ler os logs do suspeito). SEM ferramentas de domínio."),
    ("C'' · Ablação — mapa + método genérico, host pede que execute",
     "20260917-145714-rodada2-qwen3_14b",
     "Igual a C', mas com `REPROMPT_CONTINUA=1`: quando o modelo narra o plano "
     "em vez de chamar ferramenta, o host manda executar o próximo passo, em "
     "vez de forçar a conclusão. Isola o efeito do harness."),
    ("D · Rodada 2 — mapa + método + ferramentas de domínio",
     "20260915-180954-rodada2-qwen3_14b",
     "Tudo: mapa, método e as 3 ferramentas de domínio (`saude_do_pool`, "
     "`quem_esta_segurando_locks`, `mudancas_recentes`)."),
]

ANSI = re.compile(r"\x1b\[[0-9;]*m")

NOTAS = {
    "B · Ablação — só o mapa do ambiente": (
        "O mapa desenha o worker, diz que ele fala com o mesmo banco e que não "
        "aparece em trace. Ainda assim, nenhuma execução consultou os logs do "
        "worker: todas seguiram o trace do checkout, viram o pool do inventory "
        "cheio e pararam. O run_04 escreve 'operações de reconciliação longas' "
        "como uma de três hipóteses — e culpa o inventory mesmo assim. Saber que "
        "o componente existe não fez o modelo ir olhar."),
    "C · Ablação — mapa + método (o do palco)": (
        "**Confundido, e por isso existe a C'.** Todas as cinco execuções param "
        "após duas chamadas e concluem vago. Duas causas visíveis no log: (1) o "
        "filtro `|~ \"error\"` volta vazio, porque as mensagens são em português "
        "e o nível é label, não texto; (2) o método manda usar `saude_do_pool` e "
        "`quem_esta_segurando_locks`, que não existem nesta condição — sem "
        "conseguir cumprir os passos 2 e 4, o modelo pula para o 6 ('conclua'). "
        "Esta condição mede 'método que aponta para ferramenta ausente', não "
        "'método sem ferramenta'."),
    "C' · Ablação — mapa + método genérico": (
        "**Artefato do host, não do modelo.** As cinco execuções param após "
        "`list_datasources` + `list_loki_label_names`. No passo 3 o modelo "
        "respondeu em prosa ('vamos verificar os logs...') sem chamar ferramenta; "
        "o host — regra criada para segurar a rodada 1 — pede a conclusão uma "
        "única vez e encerra. Sem ter coletado nada, o modelo diz 'não há "
        "informações suficientes'. O que esta condição mostra: com ferramentas "
        "genéricas, o 14b tende a *narrar* o método em vez de *executá-lo*. Se "
        "isso é limitação do modelo ou do harness, responde a C''."),
    "C'' · Ablação — mapa + método genérico, host pede que execute": (
        "**Chamada descartada, não desistência.** Mesmo com o host mandando "
        "executar cinco vezes, o modelo devolve conteúdo vazio em ~1s — e o "
        "rastro cru mostra `eval_count=38` em todas: ele GEROU 38 tokens que o "
        "Ollama não entregou nem como texto nem como tool call. É a assinatura "
        "de uma chamada de ferramenta descartada pelo parser (nome fora da lista "
        "exposta, ou JSON que não parseou). Hipótese: o método manda 'ler os logs "
        "de quem mais escreve no banco', o modelo quer descobrir quais serviços "
        "existem e chama `list_loki_label_values`, que não está entre as 5 "
        "expostas. NÃO confirmado — exigiria replay do template cru. O que é "
        "fato: o modelo tentou algo que a interface não deixou passar, seis "
        "vezes seguidas, e o diagnóstico saiu vazio."),
}


def resolver_c() -> str | None:
    pastas = sorted(p.name for p in RES.glob("2026*-rodada2-qwen3_14b"))
    depois = [p for p in pastas if p > "20260917-145207-rodada2-qwen3_14b"]
    return depois[0] if depois else None


def passos(texto: str) -> list[str]:
    """Sequência 'ferramenta(arg=valor)' na ordem em que aconteceu."""
    saida, atual, args = [], None, []
    for linha in texto.splitlines():
        m = re.match(r"│ ferramenta: (\S+)", linha)
        if m:
            if atual:
                saida.append(f"`{atual}({', '.join(args)})`")
            atual, args = m.group(1), []
            continue
        m = re.match(r"│\s{2,}(\w+) = (.+)", linha)
        if m and atual:
            args.append(f"{m.group(1)}={m.group(2).strip()}")
    if atual:
        saida.append(f"`{atual}({', '.join(args)})`")
    return saida


def diagnostico(texto: str) -> str:
    m = re.search(r"═══ DIAGNÓSTICO.*?═══\n(.*?)\n\s*tempo de modelo: ([\d.]+)s", texto, re.S)
    if not m:
        return "(sem diagnóstico no log)", "?"
    return m.group(1).strip(), m.group(2)


def cita_worker(diag: str) -> bool:
    return bool(re.search(r"reconciliation|worker|backfill", diag, re.I))


def main() -> None:
    partes = ["# Ablação — o que exatamente fecha o gap?\n",
              "Seis condições, 5 execuções cada (mais uma exploratória, n=1), `qwen3:14b`, incidente ativo, "
              "`num_ctx=16384`. Mesma pergunta em todas: *\"O checkout-api está "
              "devolvendo erro 503 para os clientes agora. Investigue e me diga a "
              "causa raiz.\"* As condições C e C' foram adicionadas a pedido, para separar "
              "o efeito do método do efeito das ferramentas.\n",
              "Critério: o diagnóstico **nomeia o reconciliation-worker** (ou o "
              "backfill) como causa? Diagnósticos na íntegra, sem edição.\n"]
    resumo = []
    for titulo, pasta, tinha in CONDICOES:
        if pasta is None:
            pasta = resolver_c()
        if pasta is None or not (RES / pasta).exists():
            partes.append(f"\n## {titulo}\n\n_(bateria ainda não executada)_\n")
            continue
        logs = sorted((RES / pasta).glob("run_*.log"))
        acertos = 0
        bloco = [f"\n## {titulo}\n", f"**O agente tinha:** {tinha}\n",
                 f"**Pasta:** `calibracao/resultados/{pasta}/`\n"]
        if titulo in NOTAS:
            bloco.append(f"**Leitura:** {NOTAS[titulo]}\n")
        for log in logs:
            txt = ANSI.sub("", log.read_text())
            diag, tempo = diagnostico(txt)
            ok = cita_worker(diag)
            acertos += ok
            seq = passos(txt)
            bloco.append(f"\n### {log.stem} — {'✅ nomeia o worker' if ok else '❌ não nomeia o worker'} · {tempo}s de modelo\n")
            bloco.append("Caminho que seguiu:\n")
            bloco += [f"{i}. {s}" for i, s in enumerate(seq, 1)]
            bloco.append(f"\n> {diag}\n")
        resumo.append((titulo, acertos, len(logs)))
        bloco.insert(3, f"**Resultado: {acertos}/{len(logs)} nomeiam o worker.**\n")
        partes += bloco

    partes.append("""
## E · Exploratório (n=1) — C'' + `list_loki_label_values` exposta

Uma execução manual, mesma configuração de C'' mais a ferramenta
`list_loki_label_values` na lista (via `FERRAMENTAS_EXTRA`). O modelo **não
chamou** a ferramenta nova — só a presença dela no prompt mudou o caminho:

1. `list_datasources`
2. `query_loki_logs(logql={service_name="checkout-api"})`
3. `query_prometheus` ×4 (pool dos serviços)
4. `query_loki_logs(logql={service_name="inventory-api"})`
5. `query_loki_logs(logql={service_name="reconciliation-worker"})`
6. teto de 8 passos — o host força a conclusão

> O serviço **reconciliation-worker** está segurando **locks de longa
> duração** na tabela `inventory` do PostgreSQL, causando tempo de espera e
> timeout nas operações de reserva do **inventory-api**. Isso resulta em
> erros 503 no **checkout-api** [...] A evidência está nos logs do
> reconciliation-worker, que indicam que o processo está adquirindo e
> mantendo locks por 20 segundos durante o backfill.

**155,5s de modelo, 8 passos, no teto.** Chegou — com ferramentas genéricas,
mapa e método — mas em 3x o número de passos e 6x o tempo da rodada 2
(4–5 passos, 24–29s), e dependendo do host forçar a conclusão. Uma execução
não é número; é indício de que o método em prosa é *executável* com
ferramentas genéricas, e de que as ferramentas de domínio compram
confiabilidade e tempo, não possibilidade.

## Leitura geral

- **Saber que o worker existe não basta (B: 0/5).** Responde à objeção "com
  um service map a IA acharia": o mapa tinha mais do que um service map
  daria — dizia que o worker escreve no mesmo banco e não aparece em trace —
  e nenhuma execução foi olhar.
- **O método em prosa, com ferramentas genéricas, é frágil (C, C', C'': 0/5).**
  Em C aponta para ferramentas ausentes e o modelo pula para a conclusão; em
  C'' o modelo tenta algo que a interface descarta e sai vazio. O caminho
  existe (E), mas é longo e depende do host.
- **Ferramentas de domínio fecham o gap com folga (D: 5/5, 4–5 passos, ~25s).**
  Não porque tenham a resposta — `quem_esta_segurando_locks` é
  `pg_stat_activity` genérico — mas porque transformam cada passo do método
  em uma chamada óbvia. **A interface é o contexto.**
- O que esta ablação NÃO responde: se um modelo de fronteira acharia o
  worker na condição A; e se o mesmo contexto resolve um incidente diferente.
""")
    tabela = ["\n## Resumo\n", "| Condição | Nomeia o worker |", "|---|---|"]
    tabela += [f"| {t} | **{a}/{n}** |" for t, a, n in resumo]
    partes.insert(3, "\n".join(tabela) + "\n")
    (RAIZ / "calibracao/ABLACAO.md").write_text("\n".join(partes))
    print("calibracao/ABLACAO.md gerado:", [(t.split(" · ")[0], f"{a}/{n}") for t, a, n in resumo])


if __name__ == "__main__":
    main()
