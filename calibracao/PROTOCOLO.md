# Protocolo de calibração (etapa 3)

Acordado por voz em 31/08/2026. O objetivo não é fazer o agente acertar:
é provar que o comportamento das duas rodadas é **estável o bastante para
palco**. Torcida não é plano.

## Bateria

10 execuções por rodada, com `--sim` (aprovação automática), incidente
ativo durante toda a bateria (`make incidente` antes, `make curar` depois).
Cada execução é uma conversa nova, sem memória da anterior.

## Rodada 1 — o erro tem que ser bom

Pergunta padrão: por que o checkout-api está devolvendo 503?

Classificação de cada execução:

| Resultado | Definição | É o que queremos? |
|---|---|---|
| **Erro bom** | culpa inventory-api ou o banco, SEM citar o worker | sim — é o arco da palestra |
| Acerto precoce | cita o reconciliation-worker | não — estraga o antes/depois |
| Falha de modelo | trava, entra em loop, desiste ou alucina tool | não — prova a tese errada |

**Meta: ≥ 8/10 com erro bom.**

## Rodada 2 — o acerto também precisa ser confiável

Mesma pergunta, com `--com-contexto` (mapa do ambiente + método + tools de
domínio, etapa 4). Sucesso = aponta o reconciliation-worker como causa.

**Meta: ≥ 9/10.**

## Critério de troca de modelo

Se a rodada 1 ficar abaixo de 8/10 e ajuste de prompt não resolver até
**quarta 02/09**, trocar `qwen3:8b` por `qwen3:14b` (cabe nos 18G) e
recalibrar do zero. Depois de quarta, não há mais tempo de recalibrar.

## Registrar por execução

- classificação (tabela acima) e diagnóstico final (1 linha)
- nº de tool calls e quais
- tempo total de modelo (importa para o roteiro de 30 min)
- tropeços de sintaxe (LogQL/PromQL/TraceQL inválidos)

---

## Resultados (medidos em 31/08–01/09/2026)

| Rodada | Modelo | Resultado | Meta | Veredito |
|---|---|---|---|---|
| 1 (sem contexto) | qwen3:14b | **9/10 erro bom** | ≥8/10 | **APROVADA** |
| 2 (com contexto) | qwen3:8b | **9/10 apontando o worker** | ≥9/10 | **APROVADA** |

Rodada 1: 9 diagnósticos firmes culpando o inventory-api, 31–77s por
investigação. O 8b assintotou em ~4,5/10 após 5 baterias de ajuste
(60 execuções) e foi substituído conforme o critério de troca.

Rodada 2: 9 diagnósticos nomeando o reconciliation-worker, a flag
`reconciliacao.backfill=true` e os locks na tabela `inventory` — no **8b**,
o mesmo modelo que sem contexto nunca passou de 50% vago. 46–83s por
investigação (8 de 10 via conclusão forçada no teto de passos).

Em 90 execuções de rodada 1, o modelo nunca citou o worker: o desenho do
culpado invisível é estanque.

Configuração aprovada: prompt v3 + shim de tempo relativo + sanitizador de
TraceQL + reprompt/conclusão forçada + 5 tools genéricas (rodada 1) + 3
ferramentas de domínio e contexto/*.md (rodada 2).

**Decisão pendente para o roteiro:** a rodada 1 está calibrada no 14b e a
rodada 2 no 8b. Usar modelos diferentes ao vivo pode soar como truque;
medir a rodada 2 também no 14b fecharia a lacuna (bateria de ~10 min).
