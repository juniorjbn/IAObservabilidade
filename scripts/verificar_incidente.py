#!/usr/bin/env python3
"""Prova que o incidente reproduz — antes de você depender disso no palco.

Roda o ciclo completo contra a stack de pé: mede a linha de base, dispara o
backfill, mede de novo, cura, e mede a recuperação. Falha com código de saída
diferente de zero se qualquer fase não se comportar como esperado.

Só biblioteca padrão, de propósito: este script tem que rodar no seu Mac sem
venv, sem pip, sem preparação. É o comando que você executa cinco minutos
antes de subir ao palco.

    python3 scripts/verificar_incidente.py
"""

from __future__ import annotations

import os
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

CHECKOUT = "http://localhost:8001"
INVENTORY = "http://localhost:8002"
WORKER = "http://localhost:8003"

# Encurtáveis por variável de ambiente para uma conferência rápida:
#   DURACAO_AMOSTRA_S=3 ESPERA_CURA_S=2 python3 scripts/verificar_incidente.py
DURACAO_AMOSTRA_S = int(os.getenv("DURACAO_AMOSTRA_S", "10"))
CONCORRENCIA = int(os.getenv("CONCORRENCIA", "8"))
TIMEOUT_REQ_S = float(os.getenv("TIMEOUT_REQ_S", "10"))

# O worker segura os locks por HOLD_SECONDS (20s por padrão). Depois de curar,
# a transação em curso ainda precisa terminar antes do sistema respirar.
ESPERA_CURA_S = int(os.getenv("ESPERA_CURA_S", "26"))

VERDE, VERMELHO, AMARELO, NEUTRO = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


@dataclass
class Amostra:
    sucessos: int = 0
    erros: int = 0
    latencias_ms: list[float] = field(default_factory=list)
    codigos: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return self.sucessos + self.erros

    @property
    def taxa_sucesso(self) -> float:
        return (self.sucessos / self.total * 100) if self.total else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.latencias_ms:
            return 0.0
        ordenadas = sorted(self.latencias_ms)
        return ordenadas[min(int(len(ordenadas) * 0.95), len(ordenadas) - 1)]

    def resumo(self) -> str:
        detalhe = ", ".join(f"{k}={v}" for k, v in sorted(self.codigos.items()))
        return (
            f"{self.total:4d} req | sucesso {self.taxa_sucesso:5.1f}% | "
            f"p95 {self.p95_ms:7.1f}ms | {detalhe}"
        )


def _post(url: str, timeout: float = TIMEOUT_REQ_S) -> tuple[int, float]:
    inicio = time.monotonic()
    req = urllib.request.Request(url, method="POST", data=b"")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
            return resp.status, (time.monotonic() - inicio) * 1000
    except urllib.error.HTTPError as e:
        return e.code, (time.monotonic() - inicio) * 1000
    except Exception:  # noqa: BLE001  (timeout, conexão recusada, DNS)
        return 0, (time.monotonic() - inicio) * 1000


def medir(duracao_s: int) -> Amostra:
    """Bate no checkout com carga constante por `duracao_s` e tabula o resultado."""
    amostra = Amostra()
    trava = threading.Lock()
    fim = time.monotonic() + duracao_s

    def worker() -> None:
        while time.monotonic() < fim:
            codigo, ms = _post(f"{CHECKOUT}/checkout")
            with trava:
                rotulo = str(codigo) if codigo else "sem-resposta"
                amostra.codigos[rotulo] = amostra.codigos.get(rotulo, 0) + 1
                if 200 <= codigo < 300:
                    amostra.sucessos += 1
                    amostra.latencias_ms.append(ms)
                else:
                    amostra.erros += 1
            time.sleep(0.1)

    threads = [threading.Thread(target=worker) for _ in range(CONCORRENCIA)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return amostra


def esperar_saude(tentativas: int = 90) -> None:
    alvos = {"checkout-api": CHECKOUT, "inventory-api": INVENTORY,
             "reconciliation-worker": WORKER}
    print("Esperando os serviços ficarem prontos...")
    for tentativa in range(1, tentativas + 1):
        pendentes = []
        for nome, base in alvos.items():
            try:
                with urllib.request.urlopen(f"{base}/health", timeout=2) as r:
                    if r.status != 200:
                        pendentes.append(nome)
            except Exception:  # noqa: BLE001
                pendentes.append(nome)
        if not pendentes:
            print(f"  {VERDE}todos de pé{NEUTRO} ({tentativa}s)\n")
            return
        if tentativa == tentativas:
            sys.exit(f"{VERMELHO}Serviços não subiram: {', '.join(pendentes)}{NEUTRO}")
        time.sleep(1)


def controlar_backfill(acao: str) -> None:
    codigo, _ = _post(f"{WORKER}/controle/backfill/{acao}", timeout=5)
    if codigo != 200:
        sys.exit(f"{VERMELHO}Falha ao {acao} o backfill (HTTP {codigo}){NEUTRO}")


def main() -> int:
    esperar_saude()

    print("1/3  Linha de base (sistema saudável)")
    base = medir(DURACAO_AMOSTRA_S)
    print(f"     {base.resumo()}\n")

    print("2/3  Incidente: ligando o backfill do reconciliation-worker")
    controlar_backfill("ligar")
    time.sleep(4)  # deixa os locks pegarem e o pool encher
    durante = medir(DURACAO_AMOSTRA_S)
    print(f"     {durante.resumo()}\n")

    print(f"3/3  Curando e aguardando {ESPERA_CURA_S}s pela liberação dos locks")
    controlar_backfill("desligar")
    time.sleep(ESPERA_CURA_S)
    depois = medir(DURACAO_AMOSTRA_S)
    print(f"     {depois.resumo()}\n")

    verificacoes = [
        ("linha de base saudável", base.taxa_sucesso >= 95,
         f"esperado >=95% de sucesso, obtido {base.taxa_sucesso:.1f}%"),
        ("incidente degrada o serviço", durante.taxa_sucesso <= 50,
         f"esperado <=50% de sucesso durante o incidente, obtido {durante.taxa_sucesso:.1f}%"),
        ("recuperação após a cura", depois.taxa_sucesso >= 90,
         f"esperado >=90% de sucesso após curar, obtido {depois.taxa_sucesso:.1f}%"),
    ]

    print("─" * 68)
    falhou = False
    for nome, ok, detalhe in verificacoes:
        marca = f"{VERDE}PASSOU{NEUTRO}" if ok else f"{VERMELHO}FALHOU{NEUTRO}"
        print(f"  {marca}  {nome}")
        if not ok:
            print(f"          {AMARELO}{detalhe}{NEUTRO}")
            falhou = True
    print("─" * 68)

    if falhou:
        print(f"\n{VERMELHO}O incidente NÃO é confiável. Não leve isso ao palco.{NEUTRO}")
        return 1

    print(f"\n{VERDE}Incidente reprodutível.{NEUTRO} Queda de "
          f"{base.taxa_sucesso:.0f}% para {durante.taxa_sucesso:.0f}% de sucesso, "
          f"e volta para {depois.taxa_sucesso:.0f}%.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrompido; lembre de rodar `make curar`")
        sys.exit(130)
