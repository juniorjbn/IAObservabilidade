# Roteiro dos slides — fonte para o NotebookLM

Palestra: **"IAObservabilidade, como anda? Sua IA não vai resolver o incidente.
Mas pode te entregar aquele 'detalhe' que faltava."** — TDC São Paulo, 23/09/2026, 30 minutos.

Este documento é a fonte única para gerar os slides. Cada slide está delimitado
por `---` e tem a mesma estrutura: **Na tela** (o que aparece), **Destaque**
(a única frase que pode ficar grande), **Nota do apresentador** (a fala; não vai
para o slide) e **Fonte** (quando houver). Tudo em pt-BR.

## Regras para a geração

- **16 slides para 30 minutos.** Metade do tempo é demo no terminal; nesses
  blocos o slide é um pano de fundo com uma frase só, não uma explicação.
- **Pouquíssimo texto.** Máximo 4 bullets por slide, máximo 8 palavras por
  bullet. Se precisar de mais, está errado: a fala explica, o slide aponta.
- **Um destaque por slide**, em tamanho grande. Nunca dois.
- **Números grandes quando houver número.** 700 → 25. 0/10 → 9/10. O número é
  o argumento.
- **Fundo escuro.** Os slides alternam com um terminal e o Grafana; fundo claro
  faz a sala piscar a cada troca de janela.
- **Diagramas simples**, caixas e setas, monoespaçado se possível. Sem ícones
  decorativos, sem clipart, sem ilustração genérica de "IA" (nada de cérebro
  brilhante ou robô).
- **Termos técnicos ficam em inglês** (trace, pool, lock, deploy, MCP). O resto
  em português.
- Slides marcados como **[pano de fundo]** ficam atrás do terminal durante a
  demo: uma frase, nada mais.
- Slides marcados como **[cortável]** podem ser removidos se a apresentação
  atrasar; a ordem dos outros não muda.

---

## Slide 1 — Capa

**Tipo:** título
**Minuto:** 00:00

**Na tela:**
- IAObservabilidade, como anda?
- Sua IA não vai resolver o incidente.
- Mas pode te entregar aquele "detalhe" que faltava.
- Nome do palestrante · TDC São Paulo 2026

**Destaque:** "Sua IA não vai resolver o incidente."

**Nota do apresentador:** Não ler o título. Entrar direto na história da ligação
às 2h da manhã (slide 2).

---

## Slide 2 — A promessa e a ligação

**Tipo:** contraste, duas colunas
**Minuto:** 00:00–02:30

**Na tela:**
- Esquerda, "O que o fornecedor vende": *IA que resolve o incidente sozinha*
- Direita, "O que acontece às 2h": *ela não sabe nem o nome dos seus serviços*

**Destaque:** "Ela não sabe nem o nome dos seus serviços."

**Nota do apresentador:** Quem já foi acordado por plantão levanta a mão. O que
dói nunca foi a observabilidade em si — é o tempo até alguém entender o que
está acontecendo. Quando a onda de AIOps chegou prometendo resolver isso no
automático, quem está no plantão ficou com um pé atrás. Com razão.

---

## Slide 3 — A tese

**Tipo:** frase única
**Minuto:** 02:00–02:30

**Na tela:**
- O buraco não é a IA desconhecer Kubernetes.
- É desconhecer o **SEU** Kubernetes.
- O estado agora. Seus métodos. Qual fonte é a verdade.

**Destaque:** "Não é conhecer Kubernetes. É conhecer o SEU."

**Nota do apresentador:** Essa é a palestra inteira em uma frase. Tudo que vem
depois é demonstração disso. E adiantar: esse gap não se fecha com RAG — a
gente volta nisso no fim.

---

## Slide 4 — O gap tem nome

**Tipo:** dois fatos, com data
**Minuto:** 02:30–05:00

**Na tela:**
- **Gartner, março de 2025:** aposentou a categoria "AIOps Platforms". Agora é
  "Event Intelligence Solutions".
- **Thoughtworks, janeiro de 2026:** "MCP segue imaturo para operação em
  produção". Sem engenharia de contexto, vira um chat sobre dados quebrados.

**Destaque:** "Quando a própria Gartner abandona o buzzword, o hype passou do ponto."

**Nota do apresentador:** Dizer "renomeou a categoria", nunca "matou AIOps". O
motivo declarado pela Gartner: o termo virou confusão e desilusão entre líderes
de operações. A Thoughtworks fez 20 provas de conceito em mais de 16 clientes
e escreveu que o problema é entropia de contexto: cadeias que crescem sem
controle, caminhos de execução opacos. Uma frase de cada; não é slide de
leitura.

**Fonte:** Gartner, *Market Guide for Event Intelligence Solutions*, 10/03/2025.
Thoughtworks, *AIOps: What we learned in 2025*, 30/01/2026.

---

## Slide 5 — O ambiente (sem o culpado)

**Tipo:** diagrama
**Minuto:** 05:00–07:00

**Na tela:**
Diagrama de caixas e setas, monoespaçado:

```
loadgen ──> checkout-api ──> inventory-api ──> postgres
```

- checkout-api: recebe os pedidos · time de vendas
- inventory-api: reserva estoque · time de logística
- Tudo instrumentado em OpenTelemetry, stack LGTM da Grafana

**Destaque:** (nenhum; o diagrama é o slide)

**Nota do apresentador:** ATENÇÃO: este diagrama deliberadamente NÃO mostra o
`reconciliation-worker`. Ele só aparece no slide 10, na autópsia. É uma loja:
o cliente faz checkout, o checkout reserva estoque, o estoque está no
Postgres. Simples de propósito — o que importa não é a complexidade do
ambiente, é o que o modelo sabe sobre ele.

---

## Slide 6 — Nada sai da máquina

**Tipo:** três bullets + um comando
**Minuto:** 07:00–08:00

**Na tela:**
- Tudo roda **neste notebook**. Sem Wi-Fi. Sem nuvem.
- Modelo local via Ollama (qwen3, 14B de parâmetros)
- Servidor MCP oficial do Grafana em **somente leitura**:
  `mcp-grafana -disable-write`
- **Humano no portão:** cada chamada de ferramenta espera um Enter

**Destaque:** "O agente não escreve nem se quiser. E o que ele lê, passa por mim."

**Nota do apresentador:** Esse é o mesmo argumento para ambiente regulado. O
`-disable-write` derruba todas as ferramentas de escrita — dashboards,
incidentes, anotações, silêncios de alerta, até as queries SQL cruas, porque
SQL cru com credencial de escrita muta dado. NÃO afirmar "service account
Viewer": a demo roda com a credencial de admin. Se alguém perguntar "flag é
fachada": em produção a segunda camada é a credencial Viewer; aqui é demo,
está com admin, e é por isso que a flag importa — é ela que está segurando.

**Fonte:** README do grafana/mcp-grafana; `mcp-grafana --help` (1.3.0).

---

## Slide 7 — O incidente [pano de fundo]

**Tipo:** pano de fundo do terminal
**Minuto:** 08:00–09:00

**Na tela:**
- `make incidente`
- Vazão: **~700 → ~25** requisições a cada 10 segundos
- Sucesso: **100% → 0%**

**Destaque:** "700 → 25"

**Nota do apresentador:** Este slide aparece atrás do terminal, não em vez
dele. Sequência ao vivo: `make incidente`; um `curl -X POST
localhost:8001/checkout` devolvendo o 503 cru — é isso que o cliente vê;
depois o Grafana: o pool do inventory-api crava em 5, a vazão despenca. "Isso
é um plantão de verdade: 503 pro cliente, gráfico feio, e você às 2h."

**Fonte:** medido por `make verificar` no hardware do palco: 716 req/10s na
base, 0% durante (503=40), 100% após a cura.

---

## Slide 8 — Rodada 1: sem contexto [pano de fundo]

**Tipo:** pano de fundo do terminal
**Minuto:** 09:00–14:00

**Na tela:**
- RODADA 1
- 5 ferramentas genéricas: datasources, Prometheus, Loki, traces
- Nenhuma informação sobre **este** ambiente
- Cada passo passa pelo portão humano

**Destaque:** "O que ele sabe: Kubernetes. O que ele não sabe: o seu."

**Nota do apresentador:** `make agente`. Leva 1,5 a 2,5 minutos. A cada passo
aparece "Hipótese: … / Procuro: …" — ler em voz alta, é o modelo pensando.
Depois a prévia do que voltou. Costuma ir assim: "ele listou as fontes,
foi no trace do checkout, achou o inventory, foi nos logs…". Cada Enter no
portão é visível. O diagnóstico vai culpar o `inventory-api`: "sobrecarregado,
falha no backend ou conectividade".

---

## Slide 9 — Quem concorda com ele?

**Tipo:** pergunta, tela quase vazia
**Minuto:** 14:00

**Na tela:**
- Diagnóstico do agente: *"a causa raiz é o inventory-api"*
- Quem concorda?

**Destaque:** "Quem concorda com ele?"

**Nota do apresentador:** PAUSA. Deixar a sala responder. Boa parte vai
concordar — e esse é o ponto: tudo que o trace mostra aponta para o
inventory-api. É a conclusão errada mais defensável possível. Um plantonista
novo, sem contexto, faria exatamente isso.

---

## Slide 10 — Autópsia: o culpado invisível

**Tipo:** diagrama, agora completo
**Minuto:** 14:00–16:00

**Na tela:**
O mesmo diagrama do slide 5, com uma caixa nova em destaque:

```
loadgen ──> checkout-api ──> inventory-api ──> postgres
                                                  ^
                          reconciliation-worker ──┘
```

- O worker **não aparece em nenhum trace** da requisição
- Fala direto com o mesmo Postgres
- Modo backfill: transações longas segurando **lock** nas linhas de estoque
- O inventory-api bloqueia, o pool esgota, o checkout devolve 503

**Destaque:** "O dado existia desde o início. O agente nunca perguntou."

**Nota do apresentador:** Mostrar no Grafana: a métrica de pool e os logs do
worker — que estavam lá o tempo todo, inclusive a linha da mudança de
configuração `reconciliacao.backfill=true`. O agente não consultou porque não
sabia que esse serviço existia. Não é burrice do modelo. É o que qualquer um
faria sem saber quem mais fala com esse banco. NUNCA cortar este slide: sem
ele, o antes/depois vira mágica.

---

## Slide 11 — A injeção: quatro coisas

**Tipo:** lista de quatro, numerada
**Minuto:** 17:00–18:00

**Na tela:**
1. **Mapa do ambiente** — topologia, donos, qual métrica é a verdade
2. **Método de investigação** — a ordem em que o plantonista olha
3. **Ferramentas de domínio** — `saude_do_pool`, `quem_esta_segurando_locks`
4. **Mudanças recentes** — deploys, flags, config alterada

**Destaque:** "Zero RAG. Zero fine-tuning. Zero modelo novo. Quatro quilobytes."

**Nota do apresentador:** `cat contexto/mapa-do-ambiente.md` e
`metodo-de-investigacao.md` na tela, rolagem rápida. São dois arquivos
markdown que somam ~4 KB. É o que um SRE sênior contaria para um novato na
primeira semana. Ferramentas de domínio: em vez de PromQL cru, uma tool que
devolve "pool do inventory no limite, 5 de 5". A interface é o contexto.

---

## Slide 12 — Rodada 2: com contexto [pano de fundo]

**Tipo:** pano de fundo do terminal
**Minuto:** 18:00–22:00

**Na tela:**
- RODADA 2
- A mesma pergunta. O mesmo modelo.
- Mais 4 KB de contexto e 3 ferramentas de domínio.

**Destaque:** "Mesma pergunta. Mesmo modelo."

**Nota do apresentador:** `make agente-r2`. O primeiro passo leva ~45s em
silêncio: o modelo está lendo o mapa do ambiente pela primeira vez. Cobrir
com: "agora ele está lendo o que eu escrevi". Depois, ~1 min: a hipótese
evolui a cada passo até nomear o worker — ler em voz alta. Os portões
mostram `saude_do_pool`, `quem_esta_segurando_locks`, `mudancas_recentes`. O
diagnóstico nomeia o worker, a flag e os locks. `make curar` — o gráfico
volta ao vivo.

---

## Slide 13 — Não foi o modelo que cresceu [cortável]

**Tipo:** tabela de números grandes
**Minuto:** 22:00–24:00

**Na tela:**
Baterias de calibração, 10 execuções cada, nomeando o culpado certo:

| modelo | sem contexto | com contexto |
|---|---|---|
| qwen3 **8B** | **0 / 10** | **9 / 10** |
| qwen3 **14B** | **0 / 10** | **10 / 10** |

**Destaque:** "0/10 → 9/10. A única coisa que mudou foi o contexto."

**Nota do apresentador:** O que vocês viram foi o 14B. O 8B, metade do
tamanho, também acerta com contexto: 9 de 10. Sem contexto, nenhum modelo
nomeou o worker em 90 execuções — não por ser pequeno, por não ter como
saber. A tese em números: não é o tamanho do modelo, é o que ele sabe do seu
ambiente. Cortar este slide inteiro se atrasar; não encolher.

**Fonte:** `calibracao/PROTOCOLO.md`, baterias de 31/08–01/09 e
recalibração de 15/09.

---

## Slide 14 — O que isso custa

**Tipo:** três fatos, com fonte
**Minuto:** 24:00–26:30

**Na tela:**
- **Pesquisadores da Microsoft** (PACE-LM, 121 mil incidentes) precisaram
  construir um estimador de confiança: *o modelo não sabe quando não sabe*
- **Roy et al.:** dar mais documentos ao agente não melhorou; dar
  **ferramentas** melhorou a acurácia factual
- **Engenharia de contexto ≠ RAG.** Contexto é recurso finito; ferramenta
  bate documento

**Destaque:** "Ferramenta bate documento."

**Nota do apresentador:** PACE-LM mede calibração, não alucinação — se
alguém pegar no pé: "exato, e não foi o que eu afirmei; o paper mede ECE, e
reduz o erro a cerca de um terço". Roy et al.: incorporar as discussões dos
incidentes como input não trouxe ganho significativo; o agente ReAct com
ferramentas, sim. É a justificativa acadêmica do MCP. E o humano no portão
não é enfeite: é o design — o modelo não sabe quando não sabe, então alguém
que sabe precisa aprovar. Se atrasar: só PACE-LM, 1,5 min.

**Fonte:** PACE-LM, arXiv 2309.05833. Roy et al., *Exploring LLM-based
Agents for Root Cause Analysis*, arXiv 2403.04123. Anthropic, *Effective
Context Engineering for AI Agents*, 09/2025.

---

## Slide 15 — Fechamento

**Tipo:** tela escura, só o título ao final
**Minuto:** 26:30–27:30

**Na tela:**
- (tela escura durante as três frases)
- Ao final, aparece só: *"Sua IA não vai resolver o incidente. Mas pode te
  entregar aquele 'detalhe' que faltava."*

**Destaque:** o título da palestra, como última fala

**Nota do apresentador:** Três frases, sem slide, olhando para a sala:
(1) A IA não resolveu o incidente.
(2) Quem aprovou cada passo dela, e quem reverte a configuração, é você.
(3) O que ela entregou foi o detalhe que você não tinha visto — um worker que
não aparece em nenhum trace.
Só então o título aparece na tela. Fim.

---

## Slide 16 — Perguntas

**Tipo:** encerramento com referências
**Minuto:** 27:30–30:00

**Na tela:**
- Repositório da demo: github.com/juniorjbn/IAObservabilidade
- Tudo open source: OpenTelemetry · Grafana LGTM · mcp-grafana · Ollama
- Referências: Gartner 03/2025 · Thoughtworks 01/2026 · PACE-LM · Roy et al.
- Contato do palestrante

**Destaque:** (nenhum)

**Nota do apresentador:** Respostas para perguntas hostis estão prontas em
`referencias/DOSSIE.md`. Se perguntarem sobre "observabilidade de IA" (o
inverso do tema): as convenções GenAI do OpenTelemetry ainda não são
estáveis — saíram do repositório principal em junho de 2026 e até julho não
tinham release. "Observabilidade de IA" e "IA para observabilidade" são
coisas diferentes, e uma delas ainda nem tem schema.

---

## Observações para quem gera os slides

- Os slides 7, 8 e 12 são panos de fundo: uma frase, muito espaço vazio. O
  terminal vai ficar por cima deles.
- O diagrama do slide 10 é o do slide 5 com uma caixa a mais. Manter a mesma
  posição das caixas para a diferença saltar aos olhos.
- O slide 15 começa escuro e termina com o título: se a ferramenta não
  suportar animação, gerar como dois slides (15a escuro, 15b título).
- Os números do slide 13 precisam ser exatamente estes: 0/10, 9/10, 0/10,
  10/10. Não arredondar, não "aproximadamente".
