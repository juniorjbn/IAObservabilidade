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
