# Mapa do ambiente — loja (produção-demo)

## Topologia e dependências

```
loadgen ──HTTP──> checkout-api ──HTTP──> inventory-api ──SQL──> postgres (loja)
                                                                   ^
                                       reconciliation-worker ──SQL─┘
```

- **checkout-api** — recebe os pedidos dos clientes. Dono: time de vendas.
  SLO: 99% das requisições < 500ms. Grava pedidos no Postgres e reserva
  estoque chamando o inventory-api.
- **inventory-api** — controla o estoque. Dono: time de logística. Reservar
  estoque é um UPDATE na linha do SKU na tabela `inventory` (exige lock de
  linha). Pool de conexões: 5, timeout de 2s.
- **reconciliation-worker** — job de conferência de estoque. Dono: time de
  logística. NÃO recebe chamadas HTTP de ninguém e NÃO aparece em traces de
  requisição; fala direto com o MESMO banco `loja`. Em modo rotina faz uma
  conferência leve; quando a flag `reconciliacao.backfill` é ligada, roda
  backfill com transações longas.
- **postgres (loja)** — banco único compartilhado por checkout-api,
  inventory-api E reconciliation-worker. As tabelas `inventory` e `orders`.

## Fontes de verdade (o que cada sinal responde)

| Pergunta | Fonte de verdade |
|---|---|
| O pool de conexões de um serviço está saudável? | métrica `db_pool_conexoes_em_uso` vs `db_pool_capacidade` (Prometheus); esgotamento acumulado em `db_pool_esgotamentos_total` |
| Quem está travando quem no banco AGORA? | `pg_stat_activity`/`pg_locks` — ferramenta `quem_esta_segurando_locks` |
| Houve mudança de config/deploy recente? | logs com "mudança de configuração" — ferramenta `mudancas_recentes` |
| Logs por serviço | Loki, label `service_name` |
| Traces de requisição | Tempo, atributo `resource.service.name` — **lembrando que jobs sem HTTP não aparecem aqui** |

## Fatos que pegam gente nova de plantão

- O trace termina no inventory-api, mas a tabela `inventory` tem MAIS de um
  escritor. Latência ali nem sempre nasce ali.
- O pool do checkout-api quase nunca esgota (ele segura conexão por
  milissegundos); o do inventory-api esgota quando os UPDATEs bloqueiam.
