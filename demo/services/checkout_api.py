"""checkout-api — o serviço que dispara o alerta.

É aqui que o incidente APARECE, e não é aqui que ele acontece. Essa
distância é o assunto da palestra.

O pool de banco deste serviço fica saudável o tempo todo: ele segura a
conexão por milissegundos, só para gravar o pedido. Quem investigar o
checkout vai encontrar métricas de pool tranquilas e latência péssima, o
que empurra a suspeita para fora — corretamente, mas só até certo ponto.
"""

from __future__ import annotations

import logging
import os
import random

import requests
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import TimeoutError as PoolTimeout

from demo.common import db, otel

NOME_SERVICO = "checkout-api"
otel.configurar_otel(NOME_SERVICO)
otel.desligar_ruido_de_log()

log = logging.getLogger(NOME_SERVICO)

URL_INVENTORY = os.getenv("INVENTORY_URL", "http://inventory-api:8000")
TIMEOUT_INVENTORY_S = float(os.getenv("INVENTORY_TIMEOUT_S", "8"))
SKUS = [f"SKU-{n:04d}" for n in range(1, 6)]

engine = db.criar_engine(
    NOME_SERVICO,
    tamanho_pool=int(os.getenv("POOL_SIZE", "5")),
    timeout_pool=int(os.getenv("POOL_TIMEOUT_S", "2")),
)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.esperar_banco(engine)
    log.info("checkout-api pronto, falando com %s", URL_INVENTORY)
    yield


app = FastAPI(title=NOME_SERVICO, lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()
SQLAlchemyInstrumentor().instrument(engine=engine)


class PedidoCriado(BaseModel):
    pedido_id: int
    sku: str
    qtd: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/checkout", response_model=PedidoCriado)
def checkout(sku: str | None = None, qtd: int = 1) -> PedidoCriado:
    """Reserva estoque e grava o pedido.

    A reserva é uma chamada HTTP ao inventory-api; a gravação é local. Só a
    primeira etapa depende do recurso disputado.
    """
    sku = sku or random.choice(SKUS)

    try:
        resposta = requests.post(
            f"{URL_INVENTORY}/reservar",
            params={"sku": sku, "qtd": qtd},
            timeout=TIMEOUT_INVENTORY_S,
        )
    except requests.Timeout:
        log.error("timeout ao reservar estoque de %s no inventory-api", sku)
        raise HTTPException(status_code=504, detail="inventory-api não respondeu a tempo")

    if resposta.status_code >= 500:
        log.error(
            "inventory-api recusou a reserva de %s: HTTP %s", sku, resposta.status_code
        )
        raise HTTPException(status_code=503, detail="não foi possível reservar estoque")

    try:
        with engine.begin() as conexao:
            linha = conexao.execute(
                text("INSERT INTO orders (sku, qtd) VALUES (:sku, :qtd) RETURNING id"),
                {"sku": sku, "qtd": qtd},
            ).one()
    except PoolTimeout:
        db.registrar_esgotamento(NOME_SERVICO)
        log.error("pool de conexões do checkout-api esgotado ao gravar pedido")
        raise HTTPException(status_code=503, detail="banco indisponível")

    return PedidoCriado(pedido_id=linha.id, sku=sku, qtd=qtd)
