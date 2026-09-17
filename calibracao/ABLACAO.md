# Ablação — o que exatamente fecha o gap?

Seis condições, 5 execuções cada (mais uma exploratória, n=1), `qwen3:14b`, incidente ativo, `num_ctx=16384`. Mesma pergunta em todas: *"O checkout-api está devolvendo erro 503 para os clientes agora. Investigue e me diga a causa raiz."* As condições C e C' foram adicionadas a pedido, para separar o efeito do método do efeito das ferramentas.

Critério: o diagnóstico **nomeia o reconciliation-worker** (ou o backfill) como causa? Diagnósticos na íntegra, sem edição.


## Resumo

| Condição | Nomeia o worker |
|---|---|
| A · Rodada 1 — sem contexto | **0/5** |
| B · Ablação — só o mapa do ambiente | **0/5** |
| C · Ablação — mapa + método (o do palco) | **0/5** |
| C' · Ablação — mapa + método genérico | **0/5** |
| C'' · Ablação — mapa + método genérico, host pede que execute | **0/5** |
| D · Rodada 2 — mapa + método + ferramentas de domínio | **5/5** |


## A · Rodada 1 — sem contexto

**O agente tinha:** 5 ferramentas genéricas do MCP. Nenhuma informação sobre o ambiente.

**Pasta:** `calibracao/resultados/20260915-181416-rodada1-qwen3_14b/`

**Resultado: 0/5 nomeiam o worker.**


### run_01 — ❌ não nomeia o worker · 59.9s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `traceql-search(query={resource.service.name = "checkout-api"})`
3. `query_loki_logs(datasourceUid=loki, logql={job="checkout-api"})`
4. `list_loki_label_names(datasourceUid=loki)`
5. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"})`

> A causa raiz mais provável é que o serviço `inventory-api` está retornando erros HTTP 503 (Serviço Indisponível) para o `checkout-api`, causando falhas no processo de checkout. Isso indica que o `inventory-api` pode estar sobrecarregado, com falhas no backend ou com problemas de conectividade.


### run_02 — ❌ não nomeia o worker · 40.4s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `traceql-search(query={resource.service.name = "checkout-api"})`
3. `query_loki_logs(datasourceUid=loki, logql={job="checkout-api"})`
4. `list_loki_label_names(datasourceUid=loki)`
5. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"})`

> A causa raiz mais provável é que o serviço `inventory-api` está retornando erros HTTP 503 (Serviço Indisponível) ao tentar reservar SKUs, o que está causando falhas no `checkout-api`. Isso indica que o `inventory-api` pode estar sobrecarregado, com falhas no backend, ou com problemas de conectividade.


### run_03 — ❌ não nomeia o worker · 35.5s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `traceql-search(query={resource.service.name = "checkout-api"})`
3. `list_loki_label_names(datasourceUid=loki)`
4. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"})`

> A causa raiz mais provável é que o serviço `inventory-api` está retornando erros HTTP 503 (Serviço Indisponível) ao tentar reservar SKUs, o que está causando o checkout-api a falhar com um erro 503 para os clientes. Isso sugere que o `inventory-api` pode estar sobrecarregado, com falhas no backend ou com problemas de conectividade.


### run_04 — ❌ não nomeia o worker · 37.7s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `traceql-search(query={resource.service.name = "checkout-api"})`
3. `query_loki_logs(datasourceUid=loki, logql={job="checkout-api"})`
4. `list_loki_label_names(datasourceUid=loki)`
5. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"})`

> A causa raiz mais provável é um timeout ao tentar reservar estoque no serviço `inventory-api` a partir do `checkout-api`. Isso está sendo registrado como erro em logs do `checkout-api`, indicando que a comunicação entre os serviços está falhando, possivelmente devido a uma sobrecarga, latência excessiva ou falha no serviço `inventory-api`.


### run_05 — ❌ não nomeia o worker · 40.1s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `traceql-search(query={resource.service.name = "checkout-api"})`
3. `query_loki_logs(logql={job="checkout-api"}, datasourceUid=loki)`
4. `list_loki_label_names(datasourceUid=loki)`
5. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"})`

> A causa raiz mais provável é que o serviço `inventory-api` está retornando erros HTTP 503 (Serviço Indisponível) ao tentar reservar SKUs, o que está causando falhas no `checkout-api`. Isso sugere que o `inventory-api` pode estar sobrecarregado, com falhas no backend, ou com problemas de conectividade.


## B · Ablação — só o mapa do ambiente

**O agente tinha:** As mesmas 5 ferramentas + `mapa-do-ambiente.md` no system prompt (topologia com o worker desenhado, donos, tabela de fontes de verdade, 'fatos que pegam gente nova'). SEM método, SEM ferramentas de domínio.

**Pasta:** `calibracao/resultados/20260917-143925-rodada2-qwen3_14b/`

**Resultado: 0/5 nomeiam o worker.**

**Leitura:** O mapa desenha o worker, diz que ele fala com o mesmo banco e que não aparece em trace. Ainda assim, nenhuma execução consultou os logs do worker: todas seguiram o trace do checkout, viram o pool do inventory cheio e pararam. O run_04 escreve 'operações de reconciliação longas' como uma de três hipóteses — e culpa o inventory mesmo assim. Saber que o componente existe não fez o modelo ir olhar.


### run_01 — ❌ não nomeia o worker · 132.1s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `traceql-search(query={resource.service.name = "checkout-api"})`
3. `query_prometheus(datasourceUid=prometheus, expr=db_pool_conexoes_em_uso{job="checkout-api"})`
4. `query_prometheus(expr=db_pool_conexoes_em_uso{job="checkout-api"}, endTime=now, startTime=now-1h, queryType=range, stepSeconds=60, datasourceUid=prometheus)`
5. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"})`

> A causa raiz mais provável é que o **inventory-api** está retornando erro 503 (serviço indisponível) ao **checkout-api**, o que está causando o erro 503 no **checkout-api** para os clientes. Isso pode estar relacionado a problemas no **inventory-api**, como conexões esgotadas no banco de dados, bloqueios de linha no PostgreSQL ou sobrecarga no serviço.


### run_02 — ❌ não nomeia o worker · 55.0s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `traceql-search(query={resource.service.name = "checkout-api"})`
3. `query_prometheus(startTime=now-5m, queryType=instant, datasourceUid=prometheus, expr=db_pool_conexoes_em_uso{service="checkout-api"}, endTime=now)`
4. `query_prometheus(datasourceUid=prometheus, endTime=now, expr=db_pool_conexoes_em_uso{service="inventory-api"}, queryType=instant, startTime=now-5m)`
5. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"})`
6. `query_loki_logs(datasourceUid=loki, logql={service_name="inventory-api"})`

> A causa raiz mais provável é que o **inventory-api** está com o **pool de conexões esgotado**, o que está causando o erro 503 no **checkout-api**. Isso é confirmado pelos logs do **inventory-api**, que indicam que não há conexões livres disponíveis para processar as requisições de reserva de estoque, resultando em falhas no serviço.


### run_03 — ❌ não nomeia o worker · 51.5s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `traceql-search(query={resource.service.name = "checkout-api"})`
3. `query_prometheus(datasourceUid=prometheus, expr=(db_pool_conexoes_em_uso{service="checkout-api"} / db_pool_capacidade{service="checkout-api"}) * 100, queryType=instant)`
4. `query_prometheus(startTime=now-1m, datasourceUid=prometheus, expr=(db_pool_conexoes_em_uso{service="checkout-api"} / db_pool_capacidade{service="checkout-api"}) * 100, queryType=instant, endTime=now)`

> Com base nas informações coletadas até o momento, a causa raiz mais provável para o erro 503 no checkout-api é uma falha no banco de dados, especificamente no pool de conexões do inventory-api. Isso pode estar causando bloqueios ou lentidão no processamento de requisições, resultando em falhas no checkout-api.


### run_04 — ❌ não nomeia o worker · 43.1s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `traceql-search(query={resource.service.name = "checkout-api"})`
3. `query_prometheus(datasourceUid=prometheus, expr=db_pool_conexoes_em_uso{job="checkout-api"})`
4. `query_prometheus(endTime=now, startTime=now-1h, queryType=range, stepSeconds=60, datasourceUid=prometheus, expr=db_pool_conexoes_em_uso{job="checkout-api"})`
5. `query_loki_logs(logql={service_name="checkout-api"}, datasourceUid=loki)`

> A causa raiz mais provável é que o **inventory-api** está retornando erro 503 (serviço indisponível) ao **checkout-api**, o que está causando o erro 503 no **checkout-api** para os clientes. Isso pode estar relacionado a problemas no **inventory-api**, como conexões esgotadas no banco de dados, bloqueios de linha no PostgreSQL ou alta latência devido a operações de reconciliação longas.


### run_05 — ❌ não nomeia o worker · 42.7s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `traceql-search(query={resource.service.name = "checkout-api"})`
3. `query_prometheus(datasourceUid=prometheus, expr=db_pool_conexoes_em_uso{job="checkout-api"}, endTime=now, queryType=instant)`
4. `query_prometheus(queryType=instant, datasourceUid=prometheus, endTime=now, expr=db_pool_conexoes_em_uso{job="inventory-api"})`
5. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"})`

> A causa raiz mais provável é que o **inventory-api** está retornando erro 503 (serviço indisponível) ao **checkout-api**, o que está causando o erro 503 no **checkout-api** para os clientes. Isso pode estar relacionado a problemas no banco de dados, como conexões esgotadas ou bloqueios de linha no PostgreSQL, ou a falhas no próprio **inventory-api**.


## C · Ablação — mapa + método (o do palco)

**O agente tinha:** As 5 ferramentas + mapa + `metodo-de-investigacao.md` — o método da rodada 2, que cita `saude_do_pool` e `quem_esta_segurando_locks` pelo nome. SEM ferramentas de domínio.

**Pasta:** `calibracao/resultados/20260917-144726-rodada2-qwen3_14b/`

**Resultado: 0/5 nomeiam o worker.**

**Leitura:** **Confundido, e por isso existe a C'.** Todas as cinco execuções param após duas chamadas e concluem vago. Duas causas visíveis no log: (1) o filtro `|~ "error"` volta vazio, porque as mensagens são em português e o nível é label, não texto; (2) o método manda usar `saude_do_pool` e `quem_esta_segurando_locks`, que não existem nesta condição — sem conseguir cumprir os passos 2 e 4, o modelo pula para o 6 ('conclua'). Esta condição mede 'método que aponta para ferramenta ausente', não 'método sem ferramenta'.


### run_01 — ❌ não nomeia o worker · 66.7s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"} |~ "error")`

> Com base nas informações coletadas até o momento, não há evidências de logs de erro no checkout-api que possam explicar diretamente o erro 503. No entanto, como o checkout-api depende do inventory-api e do postgres, é provável que o problema esteja relacionado a uma lentidão ou bloqueio no inventory-api ou no banco de dados, causando falhas no processamento das requisições. A causa raiz mais provável é um bloqueio ou lentidão no inventory-api ou no PostgreSQL, que está afetando a capacidade do checkout-api de processar as requisições de forma eficiente.


### run_02 — ❌ não nomeia o worker · 29.8s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `query_loki_logs(logql={service_name="checkout-api"} |~ "error", datasourceUid=loki)`

> Com base nas informações coletadas até o momento, não há evidências de logs de erro no checkout-api que possam explicar diretamente o erro 503. Isso sugere que o erro pode estar relacionado a outro componente no caminho, como o inventory-api ou o banco de dados PostgreSQL, que pode estar sobrecarregado ou bloqueado por longas transações. A causa raiz mais provável é uma operação de longa duração ou bloqueio no banco de dados, que está afetando a capacidade do checkout-api de processar as requisições de forma eficiente.


### run_03 — ❌ não nomeia o worker · 29.8s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"} |~ "error")`

> Com base nas informações coletadas até o momento, a causa raiz mais provável para o erro 503 no checkout-api é a falta de logs que indicam um problema no serviço. Isso sugere que o erro pode estar relacionado a uma falha no processamento de requisições, possivelmente devido a um problema no banco de dados ou em outro componente que está causando atrasos ou falhas no checkout-api. No entanto, sem logs adicionais ou métricas específicas, não é possível determinar com certeza a causa exata.


### run_04 — ❌ não nomeia o worker · 51.4s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"} |~ "error")`

> Com base nas informações coletadas, não há logs de erro no checkout-api disponíveis no Loki para o período analisado. Isso sugere que o erro 503 pode estar sendo causado por outro componente no caminho, como o inventory-api ou o banco de dados PostgreSQL, que pode estar sobrecarregado ou bloqueado por transações longas. A causa raiz mais provável é um problema no banco de dados ou no inventory-api, que está causando atrasos ou falhas nas requisições.


### run_05 — ❌ não nomeia o worker · 28.7s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"} |~ "error")`

> Com base nas informações coletadas até o momento, não há evidências de logs de erro no checkout-api que possam explicar o problema. Isso sugere que o erro 503 pode estar sendo causado por outro componente no sistema, como o inventory-api ou o postgres (loja), que podem estar sobrecarregados ou com problemas de conexão. A causa raiz mais provável é um problema no banco de dados ou no serviço de inventário que está afetando a capacidade do checkout-api de processar as solicitações.


## C' · Ablação — mapa + método genérico

**O agente tinha:** As 5 ferramentas + mapa + `calibracao/ablacao/metodo-generico.md`: o mesmo método, reescrito sem citar ferramenta de domínio (passo 3 manda ler os logs de quem mais escreve no banco; passo 4, na falta de pg_stat_activity, ler os logs do suspeito). SEM ferramentas de domínio.

**Pasta:** `calibracao/resultados/20260917-145207-rodada2-qwen3_14b/`

**Resultado: 0/5 nomeiam o worker.**

**Leitura:** **Artefato do host, não do modelo.** As cinco execuções param após `list_datasources` + `list_loki_label_names`. No passo 3 o modelo respondeu em prosa ('vamos verificar os logs...') sem chamar ferramenta; o host — regra criada para segurar a rodada 1 — pede a conclusão uma única vez e encerra. Sem ter coletado nada, o modelo diz 'não há informações suficientes'. O que esta condição mostra: com ferramentas genéricas, o 14b tende a *narrar* o método em vez de *executá-lo*. Se isso é limitação do modelo ou do harness, responde a C''.


### run_01 — ❌ não nomeia o worker · 67.4s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `list_loki_label_names(datasourceUid=loki)`

> Não há informações suficientes para concluir a causa raiz com base no que foi coletado até o momento. É necessário investigar mais profundamente, analisando logs, métricas e traces para identificar o problema.


### run_02 — ❌ não nomeia o worker · 16.4s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `list_loki_label_names(datasourceUid=loki)`

> Não há informações suficientes para concluir a causa raiz com base no que foi coletado até o momento. É necessário investigar mais profundamente utilizando as ferramentas disponíveis.


### run_03 — ❌ não nomeia o worker · 19.2s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `list_loki_label_names(datasourceUid=loki)`

> Não há informações suficientes para concluir a causa raiz com base nos dados coletados até o momento. É necessário investigar mais profundamente, analisando logs e métricas específicas dos serviços envolvidos.


### run_04 — ❌ não nomeia o worker · 17.6s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `list_loki_label_names(datasourceUid=loki)`

> Não há informações suficientes para determinar a causa raiz com base apenas no que foi coletado até o momento. É necessário investigar mais profundamente utilizando as ferramentas disponíveis.


### run_05 — ❌ não nomeia o worker · 16.5s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `list_loki_label_names(datasourceUid=loki)`

> Não há informações suficientes para determinar a causa raiz do erro 503 no checkout-api com base nas ferramentas utilizadas até o momento. É necessário investigar mais profundamente, analisando logs, métricas e traces para identificar o problema.


## C'' · Ablação — mapa + método genérico, host pede que execute

**O agente tinha:** Igual a C', mas com `REPROMPT_CONTINUA=1`: quando o modelo narra o plano em vez de chamar ferramenta, o host manda executar o próximo passo, em vez de forçar a conclusão. Isola o efeito do harness.

**Pasta:** `calibracao/resultados/20260917-145714-rodada2-qwen3_14b/`

**Resultado: 0/5 nomeiam o worker.**

**Leitura:** **Chamada descartada, não desistência.** Mesmo com o host mandando executar cinco vezes, o modelo devolve conteúdo vazio em ~1s — e o rastro cru mostra `eval_count=38` em todas: ele GEROU 38 tokens que o Ollama não entregou nem como texto nem como tool call. É a assinatura de uma chamada de ferramenta descartada pelo parser (nome fora da lista exposta, ou JSON que não parseou). Hipótese: o método manda 'ler os logs de quem mais escreve no banco', o modelo quer descobrir quais serviços existem e chama `list_loki_label_values`, que não está entre as 5 expostas. NÃO confirmado — exigiria replay do template cru. O que é fato: o modelo tentou algo que a interface não deixou passar, seis vezes seguidas, e o diagnóstico saiu vazio.


### run_01 — ❌ não nomeia o worker · 42.0s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `list_loki_label_names(datasourceUid=loki)`

> 


### run_02 — ❌ não nomeia o worker · 29.5s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `list_loki_label_names(datasourceUid=loki)`

> 


### run_03 — ❌ não nomeia o worker · 28.5s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `list_loki_label_names(datasourceUid=loki)`

> 


### run_04 — ❌ não nomeia o worker · 28.3s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `list_loki_label_names(datasourceUid=loki)`

> 


### run_05 — ❌ não nomeia o worker · 28.5s de modelo

Caminho que seguiu:

1. `list_datasources(limit=100)`
2. `list_loki_label_names(datasourceUid=loki)`

> 


## D · Rodada 2 — mapa + método + ferramentas de domínio

**O agente tinha:** Tudo: mapa, método e as 3 ferramentas de domínio (`saude_do_pool`, `quem_esta_segurando_locks`, `mudancas_recentes`).

**Pasta:** `calibracao/resultados/20260915-180954-rodada2-qwen3_14b/`

**Resultado: 5/5 nomeiam o worker.**


### run_01 — ✅ nomeia o worker · 110.2s de modelo

Caminho que seguiu:

1. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"} |= "error")`
2. `saude_do_pool()`
3. `quem_esta_segurando_locks()`
4. `mudancas_recentes(janela_minutos=60)`

> O serviço reconciliation-worker está segurando locks no banco de dados por meio de transações longas, causando um bloqueio no inventory-api, que por sua vez está causando o erro 503 no checkout-api. A configuração reconciliacao.backfill=true está ativa, o que indica que o job de reconciliação está em modo de backfill, resultando em transações demoradas que estão travando as operações do inventory-api.


### run_02 — ✅ nomeia o worker · 24.0s de modelo

Caminho que seguiu:

1. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"} |= "error")`
2. `saude_do_pool()`
3. `quem_esta_segurando_locks()`
4. `mudancas_recentes(janela_minutos=60)`

> O serviço reconciliation-worker está segurando locks na tabela inventory com a query SELECT pg_sleep(20), o que está causando o pool do inventory-api a ficar no limite e resultando em erros 503 no checkout-api. A causa raiz provável é a configuração reconciliacao.backfill=true no reconciliation-worker, que está causando transações longas e bloqueando o inventory-api.


### run_03 — ✅ nomeia o worker · 26.0s de modelo

Caminho que seguiu:

1. `query_loki_logs(datasourceUid=loki-prod, logql={service_name="checkout-api"} |= "error")`
2. `list_datasources(type=loki)`
3. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"} |= "error")`
4. `saude_do_pool()`
5. `quem_esta_segurando_locks()`
6. `mudancas_recentes(janela_minutos=60)`

> A causa raiz mais provável é que o reconciliation-worker está executando um backfill com transações longas, o que está sobrecarregando o banco de dados e causando o erro 503 no checkout-api.


### run_04 — ✅ nomeia o worker · 24.8s de modelo

Caminho que seguiu:

1. `query_loki_logs(logql={service_name="checkout-api"} |= "error", datasourceUid=loki)`
2. `saude_do_pool()`
3. `quem_esta_segurando_locks()`
4. `mudancas_recentes(janela_minutos=60)`

> O serviço reconciliation-worker está segurando locks no banco de dados por meio de transações longas, causando o esgotamento do pool de conexões do inventory-api. Isso resulta em atrasos e erros 503 no checkout-api, que depende do inventory-api para reservar estoque. A causa raiz provável é a configuração `reconciliacao.backfill=true`, que ativa o modo de backfill com transações longas no reconciliation-worker.


### run_05 — ✅ nomeia o worker · 29.3s de modelo

Caminho que seguiu:

1. `query_loki_logs(logql={service_name="checkout-api"} |= "error", datasourceUid=loki-prod)`
2. `list_datasources(type=loki)`
3. `query_loki_logs(datasourceUid=loki, logql={service_name="checkout-api"} |= "error")`
4. `saude_do_pool()`
5. `quem_esta_segurando_locks()`

> O serviço **reconciliation-worker** está causando o bloqueio no banco de dados ao executar consultas longas (`SELECT pg_sleep(20)`), impedindo que o **inventory-api** conclua suas operações de atualização (`UPDATE inventory`). Isso resulta em conexões presas no pool do **inventory-api**, que está no limite de capacidade, causando o erro 503 no **checkout-api**. A causa raiz é o **reconciliation-worker** executando operações demoradas que bloqueiam o acesso ao banco de dados.


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
