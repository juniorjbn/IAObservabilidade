"""Instrumentação OpenTelemetry compartilhada pelos serviços da demo.

Tudo é explícito, sem o agente de auto-instrumentação. Numa palestra, o
público precisa conseguir ler o arquivo e entender de onde vem cada sinal —
e a gente precisa que o comportamento seja o mesmo em todo ensaio.

Os três sinais vão por OTLP/HTTP para o container `lgtm`, que os roteia
para Mimir (métricas), Loki (logs) e Tempo (traces).
"""

from __future__ import annotations

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Intervalo curto de propósito: no palco ninguém espera 60s por um ponto de
# métrica. É a diferença entre a demo respirar e a demo travar.
INTERVALO_EXPORT_METRICAS_MS = 5_000


def configurar_otel(nome_servico: str) -> None:
    """Liga traces, métricas e logs para um serviço.

    Idempotente na prática: cada processo chama uma vez, no arranque.
    """
    recurso = Resource.create(
        {
            "service.name": nome_servico,
            "service.namespace": os.getenv("OTEL_SERVICE_NAMESPACE", "loja"),
            "deployment.environment": os.getenv("DEPLOY_ENV", "demo"),
        }
    )

    provedor_traces = TracerProvider(resource=recurso)
    provedor_traces.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provedor_traces)

    leitor = PeriodicExportingMetricReader(
        OTLPMetricExporter(), export_interval_millis=INTERVALO_EXPORT_METRICAS_MS
    )
    metrics.set_meter_provider(MeterProvider(resource=recurso, metric_readers=[leitor]))

    provedor_logs = LoggerProvider(resource=recurso)
    provedor_logs.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))

    raiz = logging.getLogger()
    raiz.setLevel(logging.INFO)
    raiz.addHandler(LoggingHandler(level=logging.INFO, logger_provider=provedor_logs))
    raiz.addHandler(logging.StreamHandler())


def desligar_ruido_de_log() -> None:
    """Silencia o access log do uvicorn.

    Sem isso, o Loki recebe uma linha por requisição do gerador de carga e o
    sinal do incidente some no meio do barulho — o que atrapalha tanto o
    humano quanto o agente.
    """
    for nome in ("uvicorn.access", "httpx", "urllib3.connectionpool"):
        logging.getLogger(nome).setLevel(logging.WARNING)

    # O exportador OTLP tenta de novo, com backoff, enquanto o container do
    # LGTM sobe. São ~15s de retry vermelho no terminal a cada `make up`.
    # Erro de verdade continua aparecendo; só o barulho de arranque some.
    logging.getLogger("opentelemetry.exporter.otlp.proto.http").setLevel(logging.ERROR)
    logging.getLogger("opentelemetry.sdk.metrics._internal.export").setLevel(logging.ERROR)
