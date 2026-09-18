#!/bin/bash
# Checklist automático de "antes de subir" (ROTEIRO.md). Rodar na sala, 30 min
# antes. Para em qualquer falha: se parar, NÃO há palestra ao vivo — vídeo.
set -e
cd "$(dirname "$0")/.."

V="\033[32m✔\033[0m"; X="\033[31m✘\033[0m"

echo "0/6  Memória: o modelo precisa de ~11 GB dos 18"
# Em 17/09 uma bateria foi morta pelo macOS por falta de memória: Kokoro do
# VoiceMode (6,5 GB) + VM do Docker Desktop configurada com 8 GB + Chrome.
if pgrep -f "voicemode/services/(kokoro|whisper)" >/dev/null; then
  echo -e "  $X VoiceMode ligado (Kokoro/Whisper ~7 GB). Rode: voicemode service stop kokoro; voicemode service stop whisper"; exit 1
fi
DOCKER_MIB=$(grep -oi '"memorymib": *[0-9]*' ~/Library/Group\ Containers/group.com.docker/settings-store.json 2>/dev/null | grep -o '[0-9]*$')
if [ -n "$DOCKER_MIB" ] && [ "$DOCKER_MIB" -gt 4096 ]; then
  echo -e "  \033[33m!\033[0m Docker Desktop reserva ${DOCKER_MIB} MiB; os containers usam ~1,7 GB. Settings > Resources > Memory: 4 GB"
fi
LIVRE=$(memory_pressure 2>/dev/null | grep -o 'free percentage: [0-9]*' | grep -o '[0-9]*$')
if [ -n "$LIVRE" ] && [ "$LIVRE" -lt 25 ]; then
  echo -e "  $X só ${LIVRE}% de memória livre. Feche Chrome (deixe 1 aba), IDEs, Serviio."; exit 1
fi
echo -e "  $V ${LIVRE:-?}% livre, VoiceMode parado"

echo "1/6  Stack de pé?"
docker compose ps --format '{{.Name}} {{.Status}}' | grep -q "lgtm.*healthy" || { echo -e "  $X lgtm não está healthy — make subir"; exit 1; }
echo -e "  $V"

echo "2/6  Incidente reproduz? (~70s)"
make -s verificar >/dev/null || { echo -e "  $X make verificar FALHOU — vídeo, não ao vivo"; exit 1; }
echo -e "  $V"

echo "3/6  Estado limpo"
make -s curar >/dev/null; echo -e "  $V backfill desligado"

echo "4/6  Pré-aquecendo qwen3:14b com num_ctx=16384 (~40s na primeira vez)"
curl -s -m 240 http://localhost:11434/api/generate -o /dev/null \
  -d '{"model":"qwen3:14b","prompt":"ok","stream":false,"options":{"num_ctx":16384}}'
ollama ps | grep -q "qwen3:14b" && echo -e "  $V modelo carregado" || { echo -e "  $X modelo não carregou"; exit 1; }

echo "5/6  mcp-grafana e Tempo MCP respondem?"
for bin in mcp-grafana doitlive glow pandoc; do
  command -v "$bin" >/dev/null || { echo -e "  $X $bin não está no PATH (brew install $bin)"; exit 1; }
done
# GET no endpoint MCP abre um stream e nunca encerra (travou o checklist em
# 18/09). Um POST initialize, como faz um cliente de verdade, responde e sai.
curl -s -m 8 -o /dev/null -w '%{http_code}' -X POST http://localhost:3200/api/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"antes-de-subir","version":"0"}}}' \
  | grep -q "^200$" || { echo -e "  $X Tempo MCP em :3200 não respondeu ao initialize"; exit 1; }
echo -e "  $V"

echo "6/6  Abrindo o dashboard da demo (http://localhost:3000/d/loja-incidente)"
"$(dirname "$0")/grafana.sh" pool

cat <<'FIM'

──────────────────────────────────────────────
  Tudo verde. Dashboard aberto em modo kiosk, refresh de 5s (Esc mostra
  o menu se precisar). Agora, manual:
  [ ] Notificações do macOS em Não Perturbe
  [ ] iTerm: fonte grande (Cmd +), janela cheia
  [ ] Vídeo do plano B: roteiro/videos/*.mp4 aberto no QuickTime, pausado
  [ ] Slides abertos, slide 1
  [ ] Wi-Fi: pode desligar. Nada depende dele.

  Para começar:  make demo
──────────────────────────────────────────────
FIM
