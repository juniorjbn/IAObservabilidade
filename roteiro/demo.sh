#doitlive shell: /bin/zsh
#doitlive speed: 100
#doitlive commentecho: true
#doitlive prompt: {dir.cyan} ❯
#doitlive env: MODELO_OLLAMA=qwen3:14b

# ─────────────────────────────────────────────
#  demo · qualquer tecla digita · Enter executa
# ─────────────────────────────────────────────

# ▶ 07:00 · como o MCP sobe
sed -n '53,56p' agente/agente.py

# ▶ 08:00 · o incidente
make incidente

# ▶ o que o cliente vê
curl -s -X POST localhost:8001/checkout; echo

# ▶ Grafana: pool e vazão  (Cmd+Tab volta)
roteiro/grafana.sh pool

# ▶ 09:00 · RODADA 1 · 5 ferramentas, sem contexto
# ▶ ~1 min · narrar cada portão · Enter aprova
make agente

# ▶ 13:00 · pausa · quem concorda?
# ▶ autópsia · Grafana: logs no Loki  (Cmd+Tab volta)
roteiro/grafana.sh worker

# ▶ 16:00 · o contexto · rolar rápido
cat contexto/mapa-do-ambiente.md

cat contexto/metodo-de-investigacao.md

wc -c contexto/*.md

# ▶ 17:00 · RODADA 2 · mesma pergunta, mesmo modelo
# ▶ passo 1 demora ~45s · é normal
make agente-r2

# ▶ curar
make curar

# ▶ Grafana: voltou  (Cmd+Tab volta)
roteiro/grafana.sh pool

# ▶ 21:00 · fim do terminal → slides · Ctrl+C sai
