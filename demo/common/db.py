"""Engine do SQLAlchemy com o pool instrumentado.

Este arquivo é o coração da demo. O pool de conexões é o recurso que vai
esgotar, então ele precisa ser observável ANTES do incidente — senão a
palestra vira "olha que conveniente, a métrica que prova o meu ponto".

As métricas emitidas aqui existem nas duas rodadas. O que muda entre elas
não é o dado disponível: é o agente saber que ele existe e o que ele
significa neste ambiente.
"""

from __future__ import annotations

import logging
import os

from opentelemetry import metrics
from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.pool import QueuePool

log = logging.getLogger(__name__)

# Lock timeout no Postgres: uma consulta bloqueada desiste depois disso.
# Sem ele, um ensaio que der errado deixa a demo travada até você reiniciar
# tudo — o pior cenário possível no palco.
LOCK_TIMEOUT_MS = 15_000

_esgotamentos = None


def criar_engine(nome_servico: str, tamanho_pool: int, timeout_pool: int) -> Engine:
    """Cria a engine e registra os medidores do pool.

    `max_overflow=0` é deliberado: queremos um teto rígido e previsível, não
    um pool elástico que mascara a exaustão.
    """
    engine = create_engine(
        os.environ["DATABASE_URL"],
        poolclass=QueuePool,
        pool_size=tamanho_pool,
        max_overflow=0,
        pool_timeout=timeout_pool,
        pool_pre_ping=True,
        connect_args={"options": f"-c lock_timeout={LOCK_TIMEOUT_MS}"},
    )

    @event.listens_for(engine, "connect")
    def _ao_conectar(dbapi_conn, _record):  # noqa: ANN001
        log.debug("nova conexão física aberta por %s", nome_servico)

    _instrumentar_pool(engine, nome_servico)
    return engine


def _instrumentar_pool(engine: Engine, nome_servico: str) -> None:
    """Publica o estado do pool como métricas OTel.

    Gauges observáveis: o SDK chama estes callbacks a cada ciclo de export,
    então o valor sempre reflete o pool no instante da coleta.
    """
    global _esgotamentos
    medidor = metrics.get_meter("demo.db.pool")
    pool = engine.pool

    def _em_uso(_options):  # noqa: ANN001
        return [metrics.Observation(pool.checkedout(), {"service.name": nome_servico})]

    def _capacidade(_options):  # noqa: ANN001
        return [metrics.Observation(pool.size(), {"service.name": nome_servico})]

    def _ocioso(_options):  # noqa: ANN001
        return [metrics.Observation(pool.checkedin(), {"service.name": nome_servico})]

    medidor.create_observable_gauge(
        "db.pool.conexoes_em_uso",
        callbacks=[_em_uso],
        description="Conexões atualmente emprestadas do pool",
    )
    medidor.create_observable_gauge(
        "db.pool.capacidade",
        callbacks=[_capacidade],
        description="Tamanho configurado do pool",
    )
    medidor.create_observable_gauge(
        "db.pool.conexoes_ociosas",
        callbacks=[_ocioso],
        description="Conexões disponíveis no pool",
    )

    _esgotamentos = medidor.create_counter(
        "db.pool.esgotamentos",
        description="Requisições que desistiram esperando por uma conexão do pool",
    )


def registrar_esgotamento(nome_servico: str) -> None:
    """Contabiliza uma requisição que não conseguiu conexão a tempo."""
    if _esgotamentos is not None:
        _esgotamentos.add(1, {"service.name": nome_servico})


def esperar_banco(engine: Engine, tentativas: int = 30) -> None:
    """Bloqueia até o Postgres aceitar conexões.

    O `depends_on` do Compose garante ordem de arranque, não prontidão.
    """
    import time

    for tentativa in range(1, tentativas + 1):
        try:
            with engine.connect() as conexao:
                conexao.execute(text("SELECT 1"))
            return
        except Exception as erro:  # noqa: BLE001
            if tentativa == tentativas:
                raise
            log.warning("banco indisponível (tentativa %d): %s", tentativa, erro)
            time.sleep(1)
