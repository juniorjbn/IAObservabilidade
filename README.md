# IAObservabilidade

Material da palestra **"IAObservabilidade, como anda? Sua IA não vai resolver o
incidente. Mas pode te entregar aquele 'detalhe' que faltava."** (TDC).

A demo roda inteira na sua máquina. Nada sai daqui — que por acaso é o mesmo
argumento usado para ambiente regulado.

## O estado deste repositório

| Etapa | Situação |
|---|---|
| 1. Demo reproduzível (stack + incidente) | pronta e verificada |
| 2. Agente Python com MCP e portão humano | a fazer |
| 3. Calibração do erro da rodada 1 | a fazer |
| 4. Camada de contexto e ferramentas de domínio | a fazer |
| 5. Roteiro de palco minutado | a fazer |
| 6. Dossiê de referências verificadas | a fazer |

## Subir

```bash
make subir        # sobe tudo (~30s no primeiro build)
make verificar    # prova que o incidente reproduz (~70s)
```

Grafana em <http://localhost:3000> (acesso anônimo como Viewer já habilitado).

```bash
make incidente    # dispara a falha
make estado       # mostra se o incidente está ativo
make curar        # encerra
make derrubar     # apaga tudo
```

**Rode `make verificar` antes de cada apresentação.** Ele mede a linha de base,
dispara o incidente, cura, mede de novo e falha com código diferente de zero se
o comportamento não for o esperado. É a diferença entre saber e torcer.

## A topologia, e por que ela é assim

```
loadgen ──> checkout-api ──> inventory-api ──> postgres
                                                  ^
                          reconciliation-worker ──┘
```

O `reconciliation-worker` **não aparece em nenhum trace do caminho da
requisição**. Ele não recebe chamada de ninguém: fala direto com o mesmo
Postgres. Para quem investiga seguindo o trace, ele não existe.

E é ele o culpado. No modo backfill, abre uma transação longa com
`SELECT ... FOR UPDATE` sobre todas as linhas de estoque e as segura por 20
segundos. O `inventory-api` precisa dessas mesmas linhas para reservar estoque,
então suas consultas bloqueiam segurando conexão; sob carga constante o pool
dele (5 conexões, timeout de 2s) esgota em segundos e o `checkout-api` passa a
devolver 503.

### Por que esse desenho é honesto

A rodada 1 da demo mostra o agente errando. O erro precisa ser legítimo, não
fabricado, senão a plateia justificadamente desconta a demonstração inteira.

Um agente com acesso somente-leitura à observabilidade vai: ver a latência
subir no `checkout-api`, seguir o trace até o `inventory-api`, ver que é lá que
o tempo é gasto, e concluir que o `inventory-api` é o problema. Essa conclusão
está errada e é a mais defensável possível — **tudo que o trace mostra aponta
para lá**. O pool do `checkout-api`, aliás, continua saudável o tempo todo, o
que empurra a suspeita para fora corretamente, só que não longe o bastante.

O dado que resolve o incidente existe desde o primeiro segundo: o worker emite
os próprios logs e métricas, inclusive a linha que registra a mudança de
configuração que ligou o backfill. Achá-lo exige saber que esse serviço existe
e que ele divide o banco.

Isso não se resolve com um modelo maior nem com mais retrieval. Resolve-se
dizendo ao agente como *este* ambiente é montado. É a tese da palestra, e a
demo foi construída para que ela se prove sozinha.

## Métricas emitidas

Os quatro sinais do pool existem nas duas rodadas — o que muda entre elas não é
o dado disponível, é o agente saber que ele existe e o que significa aqui:

| Métrica | O que mostra |
|---|---|
| `db.pool.conexoes_em_uso` | conexões emprestadas agora |
| `db.pool.capacidade` | tamanho configurado do pool |
| `db.pool.conexoes_ociosas` | conexões livres |
| `db.pool.esgotamentos` | requisições que desistiram na fila do pool |

## Orçamento de memória

Pensado para um MacBook de 16GB com o Ollama rodando ao lado:

| Componente | RAM |
|---|---|
| `lgtm` (Prometheus, Loki, Tempo, Grafana, Collector) | 2,0 G |
| Postgres | 256 M |
| 4 processos Python | ~600 M |
| **Stack** | **~2,9 G** |

O resto fica para o modelo, que é onde a memória faz falta.

## O que foi verificado

Com Postgres real e os três serviços de pé:

```
linha de base      684 req/10s | sucesso 100,0% | p95  29,4ms
durante o incidente 25 req/10s | sucesso   0,0% | 503=20, 504=5
após a cura        658 req/10s | sucesso 100,0% | p95  32,5ms
```

Não é só a taxa de erro que muda: a vazão despenca de 684 para 25 requisições
em dez segundos. A inflexão é visível da última fila do auditório.

## Estrutura

```
demo/common/otel.py    instrumentação dos três sinais, explícita
demo/common/db.py      engine e pool instrumentado — o recurso que esgota
demo/services/         checkout-api, inventory-api, worker, gerador de carga
db/init.sql            estoque e pedidos
scripts/verificar_incidente.py   a prova de que o incidente reproduz
```
