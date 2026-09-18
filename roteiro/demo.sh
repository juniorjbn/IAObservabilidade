#doitlive shell: /bin/zsh
#doitlive speed: 100
#doitlive commentecho: true
#doitlive prompt: {dir.cyan} ❯
#doitlive env: MODELO_OLLAMA=qwen3:14b

# ─────────────────────────────────────────────
#  demo · qualquer tecla digita · Enter executa
# ─────────────────────────────────────────────

# ▶ como o MCP sobe
sed -n '/^SERVIDOR_MCP = /,/^)/p' agente/agente.py

# ▶ o incidente
make incidente

# ▶ o que o cliente vê
curl -s -X POST localhost:8001/checkout; echo

# ▶ Grafana: pool e vazão  (Cmd+Tab volta)
roteiro/grafana.sh pool

# ▶ RODADA 1 · 5 ferramentas, sem contexto
# ▶ ~2 min · ler a Hipótese de cada passo em voz alta · Enter aprova
make agente

# ▶ pausa · quem concorda?
# ▶ autópsia · Grafana: logs no Loki  (Cmd+Tab volta)
roteiro/grafana.sh worker

# ▶ o contexto · rolar rápido
cat contexto/mapa-do-ambiente.md

cat contexto/metodo-de-investigacao.md

wc -c contexto/*.md

# ▶ RODADA 2 · mesma pergunta, mesmo modelo
# ▶ passo 1 demora ~45s · é normal · depois ~1 min
make agente-r2

# ▶ curar
make curar

# ▶ Grafana: voltou  (Cmd+Tab volta)
roteiro/grafana.sh pool

# ▶ fim do terminal → slides · Ctrl+C sai
