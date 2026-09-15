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
| 2 (com contexto) | qwen3:14b | **10/10 apontando o worker** | ≥9/10 | **APROVADA** |

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

**Decisão resolvida (01/09):** a rodada 2 foi medida também no 14b: 10/10,
27–91s por investigação. O palco roda o **14b nas duas rodadas** (sem
alternância de modelo, à prova de cético); o resultado do 8b na rodada 2
vira o kicker opcional em slide — "até o modelo menor acerta, com contexto".


## 15/09/2026 — Bug de contexto encontrado e recalibração

**Achado:** o agente não fixava `num_ctx`; o Ollama usava o padrão de 4096.
Ao estourar, o llama.cpp faz "context shift" com `n_keep=4`: descarta a
primeira metade do prompt — que é onde ficam o mapa do ambiente e as
definições das ferramentas. O log do Ollama tinha 35 desses eventos, vários
datados de 01/09, **durante a calibração aprovada**. A rodada 2 só acertava
quando o modelo chegava a `saude_do_pool` antes de estourar (~passo 4).
No primeiro teste de retomada em 15/09, ela falhou: vagou para "banco de
dados ou outro serviço" sem tocar nas ferramentas de domínio.

**Correção:** `num_ctx: 16384` nas options (`agente/agente.py`). Custo:
~2,6 GB de KV cache no 14b; a máquina tem 18 GB e a stack usa ~1 GB.
Também: `export MODELO_OLLAMA ?= qwen3:14b` no Makefile — `make agente`
rodava o 8b por padrão, diferente dos vídeos e da calibração.

**Recalibração (5 execuções por rodada, 14b, incidente ativo):**

| Rodada | Resultado | Tempo de modelo (quente) | Antes |
|---|---|---|---|
| 1 (sem contexto) | **5/5 erro bom**, nenhum citou o worker | 35–60s | 31–77s |
| 2 (com contexto) | **5/5 acerto**, 4/5 citam a flag | 24–29s | 27–91s |

Log do Ollama após a correção: `n_ctx_slot = 16384`, zero context shifts,
maior prompt observado 4147 tokens (teria estourado antes). A rodada 2 ficou
~3x mais rápida — sem o shift, o prompt não é reprocessado a cada passo — e
passou a seguir o método à risca: loki → pool → locks → mudanças em 5/5.

Efeito no palco: o passo 1 da rodada 2 leva ~45s processando o system
prompt com contexto (primeira vez que o modelo o vê na sessão). É silêncio
previsível; o roteiro cobre com fala. O pré-aquecimento precisa pedir
`num_ctx=16384` no curl, senão o Ollama recarrega o modelo na rodada 1.

Resultados: `resultados/20260915-180954-rodada2-qwen3_14b/` e
`resultados/20260915-181416-rodada1-qwen3_14b/`.
