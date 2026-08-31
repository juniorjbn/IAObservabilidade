"""reconciliation-worker — o culpado invisível.

Este processo não aparece em NENHUM trace do caminho da requisição. Ele não
recebe chamada do checkout nem do inventory; fala direto com o mesmo
Postgres. Para quem investiga seguindo o trace, ele não existe.

E é ele quem, no modo backfill, abre transações longas segurando o lock das
linhas de estoque que o inventory-api precisa atualizar.

O worker emite os próprios logs e métricas. O dado está lá. Achá-lo exige
saber que este serviço existe e que ele compartilha o banco — que é
justamente o que um modelo genérico não tem como saber sobre o SEU
ambiente, e o que o mapa de topologia da rodada 2 vai entregar.
"""

from __future__ import annotations

import logging
import os
import threading
import time

from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from sqlalchemy import text

from demo.common import db, otel

NOME_SERVICO = "reconciliation-worker"
otel.configurar_otel(NOME_SERVICO)
otel.desligar_ruido_de_log()

log = logging.getLogger(NOME_SERVICO)

SKUS = [f"SKU-{n:04d}" for n in range(1, 6)]
SEGUNDOS_SEGURANDO_LOCK = int(os.getenv("HOLD_SECONDS", "20"))
INTERVALO_CICLO_NORMAL_S = int(os.getenv("INTERVALO_NORMAL_S", "30"))
PAUSA_ENTRE_CICLOS_S = int(os.getenv("PAUSA_ENTRE_CICLOS_S", "3"))

engine = db.criar_engine(
    NOME_SERVICO,
    tamanho_pool=int(os.getenv("POOL_SIZE", "2")),
    timeout_pool=int(os.getenv("POOL_TIMEOUT_S", "5")),
)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    threading.Thread(target=_laco_principal, daemon=True).start()
    yield


app = FastAPI(title=NOME_SERVICO, lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)

# O interruptor do incidente. Desligado, o worker faz o trabalho leve de
# sempre e ninguém percebe que ele existe.
_backfill_ligado = threading.Event()


def _conferencia_leve() -> None:
    """Modo normal: marca os SKUs como conferidos. Rápido, sem contenção."""
    with engine.begin() as conexao:
        conexao.execute(text("UPDATE inventory SET conferido_em = now()"))
    log.info("conferência de rotina concluída para %d SKUs", len(SKUS))


def _backfill_com_lock_longo() -> None:
    """Modo incidente: uma transação longa travando TODAS as linhas de estoque.

    `SELECT ... FOR UPDATE` sem WHERE trava a tabela inteira linha a linha; o
    `pg_sleep` mantém a transação aberta. Enquanto ela vive, todo UPDATE do
    inventory-api espera, independente do SKU sorteado pelo gerador de carga.

    Travar tudo de uma vez, e não um SKU por vez, é o que torna o incidente
    determinístico: sem isso o impacto seria proporcional à chance de sortear
    o SKU travado, e a inflexão no gráfico ficaria fraca demais para o palco.
    """
    with engine.begin() as conexao:
        conexao.execute(text("SELECT sku FROM inventory ORDER BY sku FOR UPDATE"))
        log.info(
            "backfill: lock adquirido em %d SKUs, segurando por %ds",
            len(SKUS),
            SEGUNDOS_SEGURANDO_LOCK,
        )
        conexao.execute(text("SELECT pg_sleep(:s)"), {"s": SEGUNDOS_SEGURANDO_LOCK})

    # Uma folga curta entre ciclos. Produz um dente de serra no gráfico, que é
    # como contenção de lock costuma se parecer de verdade, e evita que a demo
    # fique 100% travada sem nenhuma requisição passando.
    log.info("backfill: locks liberados, próximo ciclo em %ds", PAUSA_ENTRE_CICLOS_S)
    for _ in range(PAUSA_ENTRE_CICLOS_S):
        if not _backfill_ligado.is_set():
            return
        time.sleep(1)


def _laco_principal() -> None:
    db.esperar_banco(engine)
    log.info("reconciliation-worker iniciado em modo rotina")
    while True:
        try:
            if _backfill_ligado.is_set():
                _backfill_com_lock_longo()
            else:
                _conferencia_leve()
                # Sono fatiado: o worker acorda a cada segundo para checar o
                # interruptor. Sem isso, `make incidente` demoraria até um
                # ciclo inteiro para surtir efeito — inaceitável ao vivo.
                for _ in range(INTERVALO_CICLO_NORMAL_S):
                    if _backfill_ligado.is_set():
                        break
                    time.sleep(1)
        except Exception as erro:  # noqa: BLE001
            log.exception("ciclo do worker falhou: %s", erro)
            time.sleep(5)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/controle/status")
def status() -> dict[str, object]:
    return {
        "backfill": _backfill_ligado.is_set(),
        "segundos_segurando_lock": SEGUNDOS_SEGURANDO_LOCK,
    }


@app.post("/controle/backfill/ligar")
def ligar_backfill() -> dict[str, str]:
    """Dispara o incidente.

    O log abaixo é a pegada da mudança recente: a linha que explica o
    incidente inteiro, num serviço que ninguém está olhando.
    """
    _backfill_ligado.set()
    log.warning(
        "mudança de configuração aplicada: reconciliacao.backfill=true "
        "(janela de backfill trimestral, transações longas habilitadas)"
    )
    return {"backfill": "ligado"}


@app.post("/controle/backfill/desligar")
def desligar_backfill() -> dict[str, str]:
    _backfill_ligado.clear()
    log.warning("mudança de configuração revertida: reconciliacao.backfill=false")
    return {"backfill": "desligado"}
