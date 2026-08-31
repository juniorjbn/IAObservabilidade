"""inventory-api — onde o pool realmente esgota.

Reservar estoque exige um UPDATE na linha do SKU, o que exige o lock da
linha. Quando outra transação segura esse lock, a consulta fica bloqueada
segurando a conexão. Sob carga constante, as 5 conexões do pool ficam
presas em segundos e as requisições seguintes desistem na fila.

O agente que investigar por traces vai parar aqui e concluir que o
inventory-api é o culpado. É a conclusão errada mais defensável possível:
tudo que o trace mostra aponta para cá.
"""

from __future__ import annotations

import logging
import os

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeout

from demo.common import db, otel

NOME_SERVICO = "inventory-api"
otel.configurar_otel(NOME_SERVICO)
otel.desligar_ruido_de_log()

log = logging.getLogger(NOME_SERVICO)

engine = db.criar_engine(
    NOME_SERVICO,
    tamanho_pool=int(os.getenv("POOL_SIZE", "5")),
    timeout_pool=int(os.getenv("POOL_TIMEOUT_S", "2")),
)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.esperar_banco(engine)
    log.info("inventory-api pronto (pool=%s)", engine.pool.size())
    yield


app = FastAPI(title=NOME_SERVICO, lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)


class Reserva(BaseModel):
    sku: str
    qtd: int
    reservado_total: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/reservar", response_model=Reserva)
def reservar(sku: str, qtd: int = 1) -> Reserva:
    """Reserva `qtd` unidades de `sku`.

    O UPDATE precisa do lock da linha. É esse o ponto de contenção.
    """
    try:
        with engine.begin() as conexao:
            linha = conexao.execute(
                text(
                    "UPDATE inventory SET reservado = reservado + :qtd "
                    "WHERE sku = :sku RETURNING reservado"
                ),
                {"sku": sku, "qtd": qtd},
            ).one_or_none()
    except PoolTimeout:
        db.registrar_esgotamento(NOME_SERVICO)
        log.error(
            "pool esgotado: nenhuma conexão livre em %ss para reservar %s",
            os.getenv("POOL_TIMEOUT_S", "2"),
            sku,
        )
        raise HTTPException(status_code=503, detail="pool de conexões esgotado")
    except OperationalError as erro:
        # lock_timeout estourado: a linha estava travada por outra transação.
        log.error("consulta bloqueada ao reservar %s: %s", sku, erro.orig)
        raise HTTPException(status_code=503, detail="consulta bloqueada no banco")

    if linha is None:
        raise HTTPException(status_code=404, detail=f"sku desconhecido: {sku}")

    return Reserva(sku=sku, qtd=qtd, reservado_total=linha.reservado)
