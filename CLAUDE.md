# Contexto do projeto

Material da palestra do TDC: **"IAObservabilidade, como anda? Sua IA não vai
resolver o incidente. Mas pode te entregar aquele 'detalhe' que faltava."**

Este arquivo existe para que qualquer sessão nova — em outra máquina, outro dia
— retome o trabalho sem repetir decisões. É a mesma ideia que a palestra
defende: o gap não se fecha com um modelo maior, se fecha escrevendo o contexto
do ambiente.

## A tese

A IA não desconhece Kubernetes. Ela desconhece o *seu* Kubernetes: o estado
agora, seus métodos, qual fonte é a verdade. Esse gap não se fecha com RAG.

## Decisões travadas

| Assunto | Decisão |
|---|---|
| Duração | 30 min, demo curta e roteirizada |
| Modelo | Ollama local, 100% offline, nada sai da máquina |
| Hardware do palco | MacBook Apple Silicon, 16GB |
| App da demo | Python / FastAPI + Postgres |
| Host MCP | Agente próprio em Python (~200 linhas), não Goose nem Cline |
| Arco da demo | Antes/depois: erra sem contexto de ambiente, acerta com |
| Ferramentas na rodada 1 | **5**, genéricas. Não expor as ~20 tools do MCP do Grafana |

### O que é injetado na rodada 2

As quatro coisas, combinadas:

1. **Mapa do ambiente** — topologia, dependências, ownership, SLOs, e qual
   métrica é fonte de verdade para quê
2. **Método de investigação** — a ordem em que um humano de plantão olha as
   coisas, escrita como procedimento
3. **Ferramentas de domínio** — em vez de PromQL cru, tools como
   `saude_do_pool` e `quem_esta_segurando_locks`
4. **Mudanças recentes** — deploys, flags, config alterada na janela

### Restrições que não podem ser violadas em silêncio

- MCP do Grafana **sempre** com `--disable-write`, mais service account de leitura
- Humano no portão, visível na tela
- A demo roda offline; não pode depender do Wi-Fi do evento
- Orçamento de RAM: a stack fica em ~2,9G para sobrar memória ao modelo

## Roteiro de construção

| # | Etapa | Situação |
|---|---|---|
| 1 | Demo reproduzível (stack + incidente) | **pronta, verificada** |
| 2 | Agente Python: 5 tools, portão humano, corte de saída | **pronta, testada com o modelo real** |
| 3 | Calibração — o erro da rodada 1 tem que ser reprodutível | a fazer |
| 4 | Camada de contexto e ferramentas de domínio | a fazer |
| 5 | Roteiro de palco minutado | a fazer, só depois de medir o modelo |
| 6 | Dossiê de referências verificadas | **pronto** — `referencias/DOSSIE.md`, tudo na fonte primária |

Notas da etapa 2 (31/08/2026, testado nesta máquina):

- O mcp-grafana 1.3.0 (instalado via brew) **não tem tools de Tempo/traces**.
  As 5 tools expostas: list_datasources, list_prometheus_metric_names,
  query_prometheus, query_loki_logs, list_loki_label_values. O filtro é em
  duas camadas: `-enabled-tools datasource,prometheus,loki` no servidor +
  allowlist no host. Se a narrativa da palestra menciona "seguir o trace via
  MCP", precisa ser ajustada — traces ficam visíveis só no Grafana, não nas
  tools do agente.
- Latência do qwen3:8b (think=False): 1,6–3,1s por passo quente; ~25s no
  primeiro passo frio (carga do modelo). **Pré-aquecer o modelo antes do
  palco.** Investigação de 5 passos: ~17s de tempo de modelo.
- Tropeços observados do qwen3:8b (insumo da etapa 3): escreve LogQL inválido
  (`{service_name} |= "error"` sem valor no label), repete a mesma chamada
  errada, e desiste explicando o erro de sintaxe em vez de corrigi-lo.

A etapa 3 é a que ninguém planeja e onde mora o risco: o erro da rodada 1
precisa ser reprodutível, senão a apresentação vira torcida.

## Riscos conhecidos

- **Cadeias de 3+ ferramentas degradam em modelos locais.** É o motivo de
  expor poucas tools de alto nível em vez de PromQL cru. A interface é o
  contexto.
- **O erro da rodada 1 precisa ser de ambiente, não de burrice.** Se o modelo
  errar por ser pequeno demais, a demo prova o contrário da tese.
- **30 min é apertado** para dois ciclos de agente. Plano B: pior caso gravado
  em vídeo, pronto para cortar.
- **O título promete "aquele detalhe que faltava"**, mas o arco antes/depois
  entrega um RCA certo no final. Decidir se o fechamento reposiciona isso.

## Pesquisa já feita (agosto/2026)

Verificado, com as ressalvas que importam para não tomar pergunta hostil:

- **Gartner** aposentou "AIOps Platforms" e publicou o *Market Guide for Event
  Intelligence Solutions* em 10/03/2025.
- **Thoughtworks, "AIOps: What we learned in 2025"** — diz explicitamente que
  MCP segue imaturo para operação em produção, e descreve o problema de
  entropia de contexto.
- **PACE-LM** (arXiv 2309.05833) **não mede propensão a alucinar**. Mede
  *calibração*: reduz o ECE a 31% do baseline, sobre 121.308 incidentes.
  O paper diz "CompanyX"; a afiliação Microsoft está nos autores — dizer
  "pesquisadores da Microsoft". O 31% vale só para GPT-4 vs. baseline de
  binning uniforme; se citar número, dizer "cerca de um terço". Fraseado
  seguro no palco: "pesquisadores da Microsoft precisaram construir um
  estimador de confiança porque o modelo não sabe quando não sabe."
- **Roy et al.** (arXiv 2403.04123) achou que adicionar as *discussões dos
  incidentes* como input não melhora performance — é mais estreito que "mais
  retrieval não compra acurácia". O mesmo paper achou que o agente ReAct com
  ferramentas melhora acurácia factual. Ou seja: **ferramenta bate documento**,
  o que apoia a tese ainda melhor.
- **Convenções GenAI do OTel não estão estáveis.** Em 12/06/2026 saíram do repo
  principal (semconv v1.42.0) para `open-telemetry/semantic-conventions-genai`,
  que até julho não tinha release taggeada. Reforça a distinção entre
  "observabilidade de IA" e "IA para observabilidade".
- **`mcp-grafana` tem `--disable-write` nativo**, que desabilita
  `update_dashboard`, `create_incident`, `create_annotation` e põe o alerting
  em leitura.
- **`grafana/otel-lgtm`** roda a stack toda num container com 512Mi–2Gi.
  Fixado em `0.32.0`.

## Verificado em hardware real (31/08/2026, no Mac do palco)

As três pendências da construção em nuvem foram fechadas:

1. **Os três sinais chegam no LGTM**: métrica `db_pool_conexoes_em_uso` no
   Prometheus para os três serviços, logs do worker no Loki, traces do
   checkout no Tempo.
2. **Memória real da stack: ~1,0G** (lgtm 756M + postgres 42M + 4 Python
   ~242M), bem abaixo dos 2,9G orçados. A máquina tem 18G, não 16 — os 16
   eram margem de cautela deliberada, que agora ficou ainda maior.
3. **Build e `make verificar` passam**: 716 req/10s a 100% na linha de base,
   0% durante o incidente (503=40), 100% após a cura.

Ao vivo, o retrato do incidente confirmou o desenho: pool do inventory
cravado em 5, worker com 1 conexão (a transação longa), checkout em 0 —
a pista falsa funcionando.

Ambiente do palco: Ollama instalado via Homebrew (serviço no launchd),
modelo `qwen3:8b` baixado (5,2G).

**Cuidado com o RTK**: o proxy de tokens trunca saída de `curl` em pipe e
quebra parse de JSON. Consultas à API do Grafana devem escrever em arquivo
(`curl -o arquivo`) e ler de lá.

## Prazo, cronograma e fechamento (acordados em 31/08/2026)

**Palestra: TDC São Paulo, ~14/09/2026** (duas semanas a partir de 31/08).

- Semana 1 (até 06/09): código — calibração (etapa 3) e contexto (etapa 4).
  Se o qwen3:8b não der conta do loop, trocar de modelo até quarta 02/09.
- Semana 2 (07–13/09): palco — roteiro minutado com tempos reais, vídeo do
  plano B, 2+ ensaios completos. `make verificar` antes de cada ensaio.

**Fechamento aprovado**, em três frases: (1) a IA não resolveu o incidente;
(2) quem aprovou cada passo dela, e quem reverte a configuração, é você;
(3) o que ela entregou foi o detalhe que você não tinha visto — um worker
que não aparece em nenhum trace. O título vira a última fala.

Nota de palco: pré-aquecer o modelo antes de subir (o passo frio leva ~25s;
quente, 1,6–3,1s por passo).

## Como trabalhar aqui

```bash
make subir        # sobe a stack
make verificar    # prova que o incidente reproduz; falha com exit 1 se não
make incidente    # dispara
make curar        # encerra
```

`make verificar` antes de cada apresentação. Ele existe para você não descobrir
no palco.

Detalhes do desenho do incidente e por que ele é honesto: ver `README.md`.
