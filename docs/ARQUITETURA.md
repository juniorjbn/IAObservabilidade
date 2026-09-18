# Arquitetura da POC

Tudo roda num MacBook M3 Pro de 18 GB. Nada sai da máquina. Versões em
`make stack`; o desenho editável está em `arquitetura.excalidraw`.

```mermaid
%%{init: {"theme": "base", "themeVariables": {
  "primaryColor": "#ffffff", "primaryTextColor": "#1e1e1e", "primaryBorderColor": "#495057",
  "lineColor": "#495057", "textColor": "#1e1e1e", "titleColor": "#1e1e1e",
  "clusterBkg": "#f1f3f5", "clusterBorder": "#adb5bd",
  "edgeLabelBackground": "#ffffff", "nodeTextColor": "#1e1e1e"
}}}%%
flowchart LR
    subgraph app["APLICAÇÃO — Python 3.12 · FastAPI · OpenTelemetry SDK"]
        LG[loadgen<br/>8 req/s] -->|HTTP| CK[checkout-api<br/>pool 5]
        CK -->|HTTP /reservar| INV[inventory-api<br/>pool 5 · timeout 2s]
        INV -->|UPDATE · lock de linha| PG[(Postgres 16<br/>tabela inventory)]
        WK[reconciliation-worker<br/>backfill: FOR UPDATE 20s] -.->|SQL · sem HTTP,<br/>sem trace| PG
    end

    subgraph lgtm["grafana/otel-lgtm 0.32 — um container"]
        COL[OTel Collector<br/>OTLP/HTTP :4318]
        COL --> PROM[Prometheus 3.14<br/>métricas]
        COL --> LOKI[Loki 3.7<br/>logs]
        COL --> TMP[Tempo 3.0<br/>traces · MCP :3200]
        GRAF[Grafana 13<br/>:3000 · dashboard Loja]
    end

    CK & INV & WK -->|traces · métricas · logs| COL

    subgraph agente["AGENTE — somente leitura · humano no portão"]
        OLL[Ollama 0.33<br/>qwen3:14b Q4_K_M · num_ctx 16k]
        AG[agente/agente.py<br/>loop ReAct · portão Enter<br/>corte 2000 chars · narração lateral]
        OLL <-->|tool calls| AG
        MG[mcp-grafana 1.3<br/>-disable-write · stdio]
        TMCP[Tempo MCP<br/>streamable HTTP]
        DOM[ferramentas de domínio · rodada 2<br/>saude_do_pool<br/>quem_esta_segurando_locks<br/>mudancas_recentes]
        CTX[/contexto/*.md · ~4 KB · rodada 2<br/>mapa do ambiente<br/>método de investigação/]
        AG --> MG
        AG --> TMCP
        AG --> DOM
        CTX -->|system prompt| AG
    end

    MG -->|API · admin| GRAF
    GRAF --> PROM & LOKI & TMP
    TMCP -.->|TraceQL| TMP
    DOM -.->|pg_stat_activity · só leitura| PG
    DOM -.->|métricas · logs| GRAF

    subgraph palco["PALCO"]
        DL[doitlive<br/>roteiro/demo.sh]
        GL[glow + pandoc<br/>contexto/*.md]
        PREP[make preparar<br/>checklist + memória]
        VER[make verificar<br/>100% → 0% → 100%]
        CAL[calibração<br/>baterias de 10]
    end

    classDef vermelho fill:#ffc9c9,stroke:#c92a2a,color:#1e1e1e
    classDef azul fill:#a5d8ff,stroke:#1971c2,color:#1e1e1e
    classDef amarelo fill:#fff9db,stroke:#e67700,color:#1e1e1e
    classDef verde fill:#d3f9d8,stroke:#2b8a3e,color:#1e1e1e
    classDef roxo fill:#e5dbff,stroke:#5f3dc4,color:#1e1e1e
    classDef cinza fill:#e9ecef,stroke:#868e96,color:#1e1e1e
    class WK vermelho
    class CK,INV azul
    class COL,PROM,LOKI,TMP,GRAF amarelo
    class OLL,AG,MG,TMCP verde
    class DOM,CTX roxo
    class LG,DL,GL,PREP,VER,CAL cinza
```

## Como ler

- **O worker é o culpado e não aparece em nenhum trace da requisição** (linha
  tracejada vermelha): fala SQL direto com o mesmo Postgres. Quem segue o trace
  para no inventory-api.
- **Rodada 1:** o agente tem só `mcp-grafana` + Tempo MCP, 5 ferramentas
  genéricas, nenhuma informação sobre o ambiente. Em 90 execuções nunca nomeou
  o worker.
- **Rodada 2:** entram `contexto/*.md` (mapa + método, ~4 KB) e as três
  ferramentas de domínio. 10/10 nomeia o worker, a flag e os locks, em ~1 min.
- **Ablação** (`calibracao/ABLACAO.md`): só o mapa, 0/5; mapa + método sem as
  ferramentas, 0/5; tudo, 10/10. A interface é o contexto.
- **Somente leitura em duas frentes:** `-disable-write` no mcp-grafana (tira
  todas as tools de escrita, inclusive SQL cru) e as ferramentas de domínio
  só consultam (`pg_stat_activity`, métricas, logs). O portão humano aprova
  cada chamada.

## O que cada peça faz

| Peça | Papel | Onde |
|---|---|---|
| loadgen | 8 req/s constantes no checkout — o gráfico plano que vira despenhadeiro | `demo/services/loadgen.py` |
| checkout-api | onde o incidente **aparece**; pool sempre saudável (pista falsa) | `demo/services/checkout_api.py` |
| inventory-api | onde o pool **esgota** esperando lock | `demo/services/inventory_api.py` |
| reconciliation-worker | onde o incidente **acontece**; invisível ao trace | `demo/services/reconciliation_worker.py` |
| otel-lgtm | Collector + Prometheus + Loki + Tempo + Grafana num container | `docker-compose.yml`, `lgtm/` |
| dashboard Loja | pool, vazão, erro, logs do worker; provisionado por arquivo | `lgtm/dashboard-loja.json` |
| agente.py | o host: loop, portão, corte de saída, narração, ferramentas de domínio | `agente/agente.py` |
| mcp-grafana | datasources, Prometheus, Loki — leitura | brew, `-disable-write` |
| Tempo MCP | TraceQL nativo do Tempo 3 | `lgtm/tempo-config.yaml` |
| contexto/ | o que o modelo não tem como saber sobre *este* ambiente | `contexto/*.md` |
| calibração | baterias que provam que as duas rodadas se comportam | `calibracao/` |
| roteiro | doitlive, checklist, fala, slides, plano B | `roteiro/` |
