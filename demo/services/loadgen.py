"""Gerador de carga constante contra o checkout-api.

Carga estável importa mais do que carga alta: o incidente precisa aparecer
como uma mudança clara num gráfico plano, não como mais um pico no meio do
ruído. Quem está na quinta fila precisa enxergar a inflexão.
"""

from __future__ import annotations

import logging
import os
import threading
import time

import requests

from demo.common import otel

NOME_SERVICO = "loadgen"
otel.configurar_otel(NOME_SERVICO)
otel.desligar_ruido_de_log()

log = logging.getLogger(NOME_SERVICO)

URL_CHECKOUT = os.getenv("CHECKOUT_URL", "http://checkout-api:8000")
RPS_ALVO = float(os.getenv("RPS", "8"))
CONCORRENCIA = int(os.getenv("CONCORRENCIA", "8"))
TIMEOUT_S = float(os.getenv("TIMEOUT_S", "10"))

_intervalo_por_worker = CONCORRENCIA / RPS_ALVO


def _worker(indice: int) -> None:
    sessao = requests.Session()
    # Espalha o arranque para não disparar todas as threads no mesmo instante.
    time.sleep(_intervalo_por_worker * indice / CONCORRENCIA)
    while True:
        inicio = time.monotonic()
        try:
            sessao.post(f"{URL_CHECKOUT}/checkout", timeout=TIMEOUT_S)
        except requests.RequestException as erro:
            log.warning("requisição falhou: %s", erro)
        decorrido = time.monotonic() - inicio
        time.sleep(max(0.0, _intervalo_por_worker - decorrido))


def main() -> None:
    log.info("gerando ~%.1f req/s contra %s", RPS_ALVO, URL_CHECKOUT)
    _esperar_checkout()
    for indice in range(CONCORRENCIA):
        threading.Thread(target=_worker, args=(indice,), daemon=True).start()
    while True:
        time.sleep(3600)


def _esperar_checkout(tentativas: int = 60) -> None:
    for tentativa in range(1, tentativas + 1):
        try:
            if requests.get(f"{URL_CHECKOUT}/health", timeout=2).ok:
                return
        except requests.RequestException:
            pass
        if tentativa == tentativas:
            raise RuntimeError(f"checkout-api não respondeu em {tentativas}s")
        time.sleep(1)


if __name__ == "__main__":
    main()
