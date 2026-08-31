# Dossiê de referências verificadas

Cada referência da palestra, verificada na fonte primária em **31/08/2026**.
Formato: fonte → citação exata → fraseado seguro de palco → pergunta hostil
mais provável e resposta. O fraseado de palco é o teto: dizer menos que ele é
seguro, dizer mais é aposta.

---

## 1. Gartner — fim da categoria "AIOps Platforms"

**Fonte primária:** Gartner, *Market Guide for Event Intelligence Solutions*,
documento G00806237/6250551, publicado em **10/03/2025**, autores **Matt
Crossley e Gregg Siegfried**.
<https://www.gartner.com/en/documents/6250551>

O guide é pago. O que é verificável publicamente:

- A página do documento na Gartner confirma título e existência
  (o conteúdo fica atrás do paywall; o site bloqueia acesso automatizado).
- Reprints licenciados por vendors confirmam data, autores e conteúdo:
  [PagerDuty](https://www.pagerduty.com/resources/analyst-reports/analyst-report/gartner-market-guide-for-event-intelligence-solutions/),
  [BigPanda](https://www.bigpanda.io/ar-gartner-event-intelligence-solutions/),
  [Selector](https://www.selector.ai/newsroom/selector-identified-by-gartner-as-a-representative-vendor-in-the-2025-market-guide-for-event-intelligence-solutions/).
- A definição pública de EIS: ferramentas que aplicam IA e analytics para
  "augment, accelerate, and automate responses to signals or events detected
  from digital services" (*aumentar, acelerar e automatizar respostas a sinais
  ou eventos detectados de serviços digitais*).

**O que a fonte afirma:** a Gartner deixou de publicar o *Market Guide for
AIOps Platforms* e passou a cobrir o mercado sob o nome *Event Intelligence
Solutions*, citando uso excessivo do termo "AIOps" por vendors e desilusão
de líderes de infraestrutura e operações.

**Fraseado seguro de palco:**
> "Em março de 2025 a Gartner parou de publicar o Market Guide de 'AIOps
> Platforms' e renomeou a categoria para Event Intelligence Solutions. Não é
> que AIOps morreu — é que o termo foi tão inflado por marketing que a própria
> Gartner desistiu dele."

**Não dizer:** "a Gartner declarou AIOps morto" ou "a Gartner desistiu de IA
em operações". As capacidades (correlação, detecção de anomalia, GenAI)
continuam no guide novo — mudou o rótulo e o enquadramento.

**Pergunta hostil provável:** *"Você leu o guide ou está citando blog de
vendor?"*
**Resposta:** "O guide é pago; o que afirmo é o que é público e confirmado
por reprints licenciados: título, data de 10/03/2025, autores, e que ele
substitui o guide de AIOps Platforms. A frase sobre inflação do termo está
no texto reproduzido pelos reprints oficiais. Se alguém aqui tem assinatura
Gartner, confere em dois minutos — documento 6250551."

---

## 2. Thoughtworks — MCP imaturo para produção; entropia de contexto

**Fonte primária:** Zichuan Xiong, *"AIOps: What we learned in 2025"*,
blog da Thoughtworks, publicado em **30/01/2026**.
<https://www.thoughtworks.com/en-us/insights/blog/generative-ai/aiops-what-we-learned-in-2025>

**Citações exatas (verificadas no artigo):**

> "current agent communication protocols such as MCP remain immature for
> production-grade operations"

*(protocolos atuais de comunicação entre agentes, como o MCP, seguem imaturos
para operações em nível de produção)*

> "Context chains grow uncontrollably. Orchestration becomes highly complex.
> Execution paths are opaque."

*(cadeias de contexto crescem sem controle; a orquestração fica altamente
complexa; os caminhos de execução são opacos)* — é a descrição do problema
de **entropia** que o artigo relata em cenários complexos.

> "Across more than 16 clients, we delivered 20 PoCs for real IT operations
> with eleven reaching production"

*(em mais de 16 clientes, entregamos 20 PoCs de operações de TI reais, com
onze chegando a produção)*

**Fraseado seguro de palco:**
> "A Thoughtworks rodou 20 PoCs de AIOps em 16 clientes em 2025 — 11 chegaram
> a produção — e o balanço deles diz com todas as letras: MCP segue imaturo
> para operação em produção, e cadeias de contexto crescem sem controle. É
> experiência de campo, não opinião de palco."

**Pergunta hostil provável:** *"Se o MCP é imaturo, por que sua demo usa
MCP?"*
**Resposta:** "Porque a imaturidade que eles descrevem é exatamente o que a
demo endereça: cadeia de contexto sem controle e execução opaca. Por isso o
agente expõe 5 tools em vez de 20, roda com `--disable-write`, e tem um
humano aprovando cada chamada na tela. A demo não contradiz o achado — ela é
a mitigação dele."

**Nota de precisão:** o artigo é de janeiro de 2026 *sobre* 2025. Se citar
data, dizer "publicado em janeiro de 2026, sobre o aprendizado de 2025".

---

## 3. PACE-LM — calibração de confiança, não alucinação

**Fonte primária:** Zhang, Zhang, Bansal, Las-Casas, Fonseca, Rajmohan,
*"PACE-LM: Prompting and Augmentation for Calibrated Confidence Estimation
with GPT-4 in Cloud Incident Root Cause Analysis"*, arXiv 2309.05833 (v3,
29/09/2023). <https://arxiv.org/abs/2309.05833>

Cinco dos seis autores têm afiliação **Microsoft** (o primeiro autor é da
UIUC). O paper anonimiza a empresa como "CompanyX" — **não** escreve
"Microsoft" no texto.

**Citações exatas (verificadas no paper):**

> "their effectiveness in assisting on-call engineers is constrained by low
> accuracy due to the intrinsic difficulty of the task, a propensity for
> LLM-based approaches to hallucinate, and difficulties in distinguishing
> these well-disguised hallucinations"

*(a efetividade em ajudar engenheiros de plantão é limitada pela baixa
acurácia — dada a dificuldade intrínseca da tarefa —, pela propensão de
abordagens baseadas em LLM a alucinar, e pela dificuldade de distinguir essas
alucinações bem disfarçadas)*

> "we propose to perform confidence estimation for the predictions to help
> on-call engineers make decisions on whether to adopt the model prediction"

*(propomos estimar a confiança das predições para ajudar engenheiros de
plantão a decidir se adotam a predição do modelo)*

> "a total of 121,308 incidents"

*(dados de incidentes de diferentes serviços e severidades dentro da
CompanyX, totalizando 121.308 incidentes)*

**A conta do "31% do baseline" (Tabela 2, verificada):** com GPT-4-8K como
gerador de causa raiz, o ECE do método completo é **0,082** contra **0,261**
do baseline de binning uniforme — 0,082/0,261 = **31,4%**. Ou seja: o número
está certo, mas vale para *essa* comparação (GPT-4 vs. baseline uniforme);
outros pares dão razões diferentes (0,084/0,327 = 26% no GPT-3.5).

**O que a fonte NÃO afirma:** que mede propensão a alucinar. Alucinação
aparece como *motivação*; a métrica é **ECE** (Expected Calibration Error) —
o quanto a confiança declarada bate com a acurácia real.

**Fraseado seguro de palco (o já acordado, que segue válido):**
> "A Microsoft precisou construir um estimador de confiança porque o modelo
> não sabe quando não sabe."

Se quiser o número: "pesquisadores da Microsoft, sobre um corpus de mais de
120 mil incidentes, reduziram o erro de calibração a cerca de um terço do
baseline." Não dizer "reduziu alucinação em 69%".

**Pergunta hostil provável:** *"Esse paper não prova que LLM alucina em
RCA — ele nem mede isso."*
**Resposta:** "Exato, e não é o que eu afirmei. O paper mede calibração: ECE.
O ponto que uso é anterior à métrica: a própria motivação do trabalho, escrita
no abstract, é que as alucinações são 'bem disfarçadas' e o engenheiro não
consegue distingui-las — por isso precisaram de um estimador de confiança
separado do modelo. O modelo não sabe quando não sabe; alguém teve que medir
por fora."

---

## 4. Roy et al. — ferramenta bate documento

**Fonte primária:** Roy, Zhang, Bhave, Bansal, Las-Casas, Fonseca, Rajmohan,
*"Exploring LLM-based Agents for Root Cause Analysis"*, arXiv 2403.04123
(07/03/2024). <https://arxiv.org/abs/2403.04123>

Mesmo time da Microsoft do PACE-LM. Avaliação sobre "an out-of-distribution
dataset of production incidents collected at Microsoft" (*incidentes de
produção coletados na Microsoft*) — aqui a Microsoft é nomeada.

**Citações exatas (verificadas no paper):**

> "incorporating discussions associated with incident reports as additional
> inputs for the models, which surprisingly does not yield significant
> performance improvements"

*(incorporar as discussões associadas aos relatórios de incidente como input
adicional, surpreendentemente, não traz melhora significativa de performance)*

> "ReAct performs competitively with strong retrieval and reasoning
> baselines, but with highly increased factual accuracy"

*(o ReAct performa de forma competitiva com baselines fortes de retrieval e
raciocínio, mas com acurácia factual muito maior)*

**Fraseado seguro de palco:**
> "O mesmo time da Microsoft testou dar mais documento ao modelo — as
> discussões dos incidentes — e não melhorou. Deram um agente com
> ferramentas, e a acurácia factual subiu muito. Ferramenta bate documento."

**Limite do fraseado:** o achado sobre discussões é estreito — vale para
*aquele* input, *aquele* dataset. Não generalizar para "RAG não funciona".
O que se pode dizer: "no experimento deles, mais retrieval não comprou
acurácia; agir sobre o ambiente comprou".

**Pergunta hostil provável:** *"O ReAct 'performa competitivamente', não
melhor. Você está esticando o resultado."*
**Resposta:** "A frase completa do paper é: competitivo com os baselines,
'but with highly increased factual accuracy'. Em RCA, acurácia factual é o
que importa — um RCA plausível e factualmente errado é o pior resultado
possível, porque manda o plantão cavar no lugar errado. Empatar em score e
alucinar menos é ganhar."

---

## 5. Convenções GenAI do OpenTelemetry — instáveis, e mudaram de casa

**Fontes primárias:**

- Release **v1.42.0** do `open-telemetry/semantic-conventions`, **12/06/2026**:
  <https://github.com/open-telemetry/semantic-conventions/releases/tag/v1.42.0>
- Repo novo: <https://github.com/open-telemetry/semantic-conventions-genai>

**Citação exata (release notes v1.42.0, verificada):**

> "All `gen_ai.*` attributes, metrics, events, and spans previously defined
> under `model/gen-ai/`, `model/openai/`, and `model/mcp/` (and documented
> under `docs/gen-ai/`) are deprecated in this repository and have moved to
> the OpenTelemetry GenAI semantic conventions repository."

*(todos os atributos, métricas, eventos e spans `gen_ai.*` estão deprecados
neste repositório e foram movidos para o repositório de convenções semânticas
GenAI)* — listada como **breaking change**.

**Re-verificado em 31/08/2026:** o repo novo tem **zero releases e zero
tags** (conferido na página de releases e na API de tags do GitHub). O README
tem "Schema URL: TODO". Nada mudou desde julho — o dado da palestra segue
válido. **Conferir de novo na véspera**; se sair uma release nas próximas
duas semanas, o fraseado vira "a primeira release saiu semana passada", o
que sustenta o mesmo ponto.

**Fraseado seguro de palco:**
> "Em junho de 2026 as convenções GenAI saíram do repositório principal do
> OpenTelemetry como breaking change, para um repo próprio que até hoje
> [conferir na véspera] não tem uma release taggeada. Nem o vocabulário para
> *observar* IA está estável — o que ajuda a separar as duas conversas:
> observabilidade de IA e IA para observabilidade."

**Pergunta hostil provável:** *"Mover de repo é reorganização, não sinal de
imaturidade. O OTel faz isso para iterar mais rápido."*
**Resposta:** "Concordo que o motivo é velocidade de iteração — e é
exatamente o ponto: precisar iterar rápido é o oposto de estável. As release
notes marcam a mudança como breaking change, os atributos `gen_ai.*` foram
deprecados no repo principal, e o repo novo não tem release taggeada. Quem
instrumentou contra a convenção antiga quebrou. Isso é, por definição, um
vocabulário ainda em movimento."

---

## 6. mcp-grafana com `--disable-write`

**Fontes primárias:** README do repo
(<https://github.com/grafana/mcp-grafana>) e o binário instalado nesta
máquina (`mcp-grafana --help`, brew, 1.3.0) — conferem entre si.

**Citação exata (help do binário, verificada localmente):**

> `-disable-write    Disable write tools (create/update operations)`

**O que desabilita, de fato:** *todas* as tools de escrita — mais do que as
três que o CLAUDE.md cita como exemplo. A lista do README inclui:
`update_dashboard`; `create_incident`, `add_activity_to_incident`,
`update_incident`; `alerting_manage_rules` e `alerting_manage_silences`
(alerting vira só leitura); `update_alert_group`; `create_annotation`,
`update_annotation`; `create_snapshot`, `delete_snapshot`; e — detalhe que
vale ouro numa pergunta — **as tools de SQL cru** (`query_clickhouse`,
`query_snowflake`, `query_athena`, `query_influxdb`), porque uma query
passada sem filtro pode mutar dados se a credencial do datasource permitir.
Existe flag explícita para retê-las sob `--disable-write`, apenas quando a
credencial é comprovadamente read-only.

**Service account:** o README recomenda RBAC por tool; para operação
somente-leitura, **Viewer role**. A alternativa "simples" que ele oferece
(Editor) é para quem usa as tools de escrita — não é o nosso caso. A demo
usa as duas camadas: `--disable-write` no servidor + service account Viewer.

**Fraseado seguro de palco:**
> "O servidor MCP oficial do Grafana tem um `--disable-write` nativo que
> derruba todas as ferramentas de escrita — dashboards, incidentes,
> anotações, silêncios de alerta, até as queries SQL cruas, porque SQL cru
> com credencial de escrita muta dado. E por baixo disso, o service account
> é Viewer. Defesa em duas camadas: o agente não escreve nem se quiser."

**Pergunta hostil provável:** *"Flag no servidor é proteção de fachada — se
o token tem escrita, o agente acha outro caminho."*
**Resposta:** "Por isso são duas camadas independentes: a flag remove as
tools do lado do servidor MCP, e o token é de um service account Viewer —
mesmo que a flag falhasse, a API do Grafana negaria a escrita. E há a
terceira camada, visível na tela: cada chamada passa por aprovação humana
antes de executar."

---

## Extras

### Números da nossa própria demo

Medidos por `scripts/verificar_incidente.py` (`make verificar`), com Postgres
real e os três serviços de pé — rodar de novo antes de cada apresentação:

| Fase | Vazão | Sucesso | Latência |
|---|---|---|---|
| Linha de base | 684 req/10s | 100,0% | p95 29,4ms |
| Durante o incidente | 25 req/10s | 0,0% | 503=20, 504=5 |
| Após a cura | 658 req/10s | 100,0% | p95 32,5ms |

No hardware do palco (31/08/2026): 716 req/10s na base, 0% durante o
incidente (503=40), 100% após a cura. Memória real da stack: **~1,0G**
(orçado: 2,9G). O ponto de palco: não é só a taxa de erro — a vazão despenca
de ~700 para ~25 req/10s; a inflexão é visível da última fila.

### Engenharia de contexto vs. RAG

Duas fontes técnicas de peso, alinhadas com a tese sem serem listicle:

**Anthropic, *"Effective Context Engineering for AI Agents"* (29/09/2025)**
<https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>

> "Context, therefore, must be treated as a finite resource with diminishing
> marginal returns."

*(contexto deve ser tratado como recurso finito, com retornos marginais
decrescentes)* — nomeia o fenômeno de **context rot**: quanto mais tokens na
janela, pior a capacidade do modelo de recuperar informação dela. E defende
a abordagem *just in time*: em vez de pré-processar tudo, o agente mantém
identificadores leves e carrega dados sob demanda **via ferramentas** — que é
exatamente o desenho da rodada 2 da demo (mapa curto + tools de domínio, não
um dump de runbooks).

**Yichao 'Peak' Ji, *"Context Engineering for AI Agents: Lessons from
Building Manus"* (18/07/2025)**
<https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus>

Relato de produção: a Manus apostou em engenharia de contexto em vez de
fine-tuning depois de queimar semanas por iteração em modelos próprios que o
lançamento seguinte tornava obsoletos —

> "If model progress is the rising tide, we want Manus to be the boat, not
> the pillar stuck to the seabed."

*(se o progresso dos modelos é a maré subindo, queremos ser o barco, não o
pilar fincado no fundo)* — o argumento da palestra em uma frase: o gap não se
fecha esperando o modelo maior; fecha-se escrevendo o contexto do ambiente,
que sobrevive à troca de modelo.

---

## Mudanças que este dossiê impõe ao fraseado da palestra

1. **PACE-LM / "Microsoft"**: o paper diz "CompanyX"; a afiliação Microsoft
   está nos autores. Usar "pesquisadores da Microsoft", não "a Microsoft
   publicou dados dos seus incidentes". O "31% do baseline" vale para
   GPT-4 vs. binning uniforme — se citar o número, citar assim ou arredondar
   para "cerca de um terço".
2. **Gartner**: dizer "renomeou a categoria", nunca "matou AIOps".
3. **Thoughtworks**: artigo publicado em **janeiro de 2026**, sobre 2025.
4. **mcp-grafana**: `--disable-write` desabilita mais do que os três
   exemplos do CLAUDE.md — inclusive SQL cru. Isso *fortalece* o argumento;
   usar a lista completa.
5. **OTel GenAI**: status re-verificado em 31/08/2026 (zero releases). Marcar
   re-verificação na véspera da palestra.
