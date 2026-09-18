# Comandos da demo. Os nomes são os que você vai digitar no palco, então são
# curtos e em português — errar de dedo às 14h com 300 pessoas olhando é caro.

SHELL := /bin/bash
COMPOSE := docker compose

.DEFAULT_GOAL := ajuda

.PHONY: ajuda subir derrubar incidente curar estado verificar logs painel reiniciar preparar demo stack agente agente-r2

ajuda:  ## Lista os comandos disponíveis
	@grep -hE '^[a-z0-9-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

subir:  ## Sobe a stack inteira (LGTM, Postgres, serviços, carga)
	$(COMPOSE) up -d --build
	@echo
	@echo "Grafana:  http://localhost:3000"
	@echo "Aguarde ~30s e rode 'make verificar' para conferir se o incidente reproduz."

derrubar:  ## Derruba tudo e apaga os volumes
	$(COMPOSE) down -v

reiniciar: derrubar subir  ## Estado limpo do zero

incidente:  ## Dispara o incidente (backfill do reconciliation-worker)
	@curl -sS -X POST http://localhost:8003/controle/backfill/ligar | tee /dev/null
	@echo " <- backfill ligado; a degradação aparece no Grafana em segundos"

curar:  ## Encerra o incidente
	@curl -sS -X POST http://localhost:8003/controle/backfill/desligar | tee /dev/null
	@echo " <- backfill desligado; o sistema volta quando a transação atual fechar"

estado:  ## Mostra se o incidente está ativo e a saúde dos serviços
	@echo -n "worker:        "; curl -sS http://localhost:8003/controle/status || true
	@echo
	@echo -n "checkout-api:  "; curl -sS http://localhost:8001/health || true
	@echo
	@echo -n "inventory-api: "; curl -sS http://localhost:8002/health || true
	@echo

verificar:  ## Prova que o incidente reproduz (~70s). Rode antes de cada apresentação.
	@python3 scripts/verificar_incidente.py

preparar:  ## Checklist completo de antes de subir (memória, stack, incidente, modelo, MCPs, Grafana)
	@roteiro/antes-de-subir.sh

demo:  ## A demo ao vivo com doitlive (qualquer tecla digita, Enter executa)
	@doitlive play roteiro/demo.sh

logs:  ## Acompanha os logs dos serviços da aplicação
	$(COMPOSE) logs -f checkout-api inventory-api reconciliation-worker

stack:  ## Mostra a stack inteira com versões, lida do que está rodando
	@scripts/stack.sh

painel:  ## Abre o Grafana
	@python3 -c "import webbrowser; webbrowser.open('http://localhost:3000')"

# Modelo do palco. Os vídeos do plano B e a calibração rodaram com 14b;
# sem isto, o agente cai no padrão do código (8b) e a rodada 1 vaga.
export MODELO_OLLAMA ?= qwen3:14b

agente:  ## Rodada 1: agente investiga SEM contexto de ambiente
	agente/.venv/bin/python agente/agente.py

agente-r2:  ## Rodada 2: agente investiga COM contexto de ambiente
	agente/.venv/bin/python agente/agente.py --com-contexto
