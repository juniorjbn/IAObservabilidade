#!/bin/bash
# Imprime a stack inteira da demo, com versões, lida do que está rodando —
# não de um arquivo que envelhece. Serve para o slide "nada sai da máquina" e
# para responder "que versão você usou?" no Q&A sem chutar.
G="http://localhost:3000/api/datasources/proxy/uid"
v() { curl -s -m 3 "$1" | python3 -c "import sys,json;d=json.load(sys.stdin);print((d.get('data') or d).get('version','?'))" 2>/dev/null || echo "?"; }
ROW() { printf "  %-22s %-28s %s\n" "$1" "$2" "$3"; }

echo
echo "  MÁQUINA"
ROW "hardware"   "$(sysctl -n machdep.cpu.brand_string), $(( $(sysctl -n hw.memsize) / 1073741824 )) GB" "macOS $(sw_vers -productVersion)"
echo
echo "  MODELO (local, offline)"
ROW "ollama"     "$(ollama --version 2>/dev/null | grep -o '[0-9][0-9.]*')" "http://localhost:11434"
ROW "modelo"     "${MODELO_OLLAMA:-qwen3:14b}" "$(ollama show ${MODELO_OLLAMA:-qwen3:14b} 2>/dev/null | awk '/parameters/{p=$2} /quantization/{q=$2} END{print p", "q", num_ctx 16384"}')"
echo
echo "  OBSERVABILIDADE (grafana/otel-lgtm $(docker inspect lgtm --format '{{.Config.Image}}' 2>/dev/null | cut -d: -f2), um container)"
ROW "grafana"    "$(curl -s -m 3 http://localhost:3000/api/health | python3 -c 'import sys,json;print(json.load(sys.stdin)["version"])' 2>/dev/null)" "dashboards, datasources"
ROW "prometheus" "$(v $G/prometheus/api/v1/status/buildinfo)" "métricas (db.pool.*, http.server.*)"
ROW "loki"       "$(v $G/loki/loki/api/v1/status/buildinfo)" "logs"
ROW "tempo"      "$(v $G/tempo/api/status/buildinfo)" "traces + MCP nativo em :3200"
ROW "otel collector" "(embutido no otel-lgtm)" "OTLP/HTTP :4318"
echo
echo "  APLICAÇÃO (instrumentada em OpenTelemetry)"
read -r PY OTEL FA SA < <(docker exec checkout-api python -c "import sys,importlib.metadata as m;print(sys.version.split()[0], m.version('opentelemetry-sdk'), m.version('fastapi'), m.version('sqlalchemy'))" 2>/dev/null)
ROW "python"     "$PY" "checkout-api, inventory-api, reconciliation-worker, loadgen"
ROW "opentelemetry-sdk" "$OTEL" "traces, métricas e logs, explícito"
ROW "fastapi / sqlalchemy" "$FA / $SA" "pool: 5 conexões, timeout 2s"
ROW "postgres"   "$(docker exec postgres psql -U demo -d loja -tAc 'show server_version' 2>/dev/null)" "um banco, três escritores"
echo
echo "  AGENTE (somente leitura, humano no portão)"
ROW "mcp-grafana" "$(brew list --versions mcp-grafana 2>/dev/null | awk '{print $2}')" "-disable-write, categorias datasource/prometheus/loki"
ROW "python (agente)" "$(agente/.venv/bin/python -c 'import sys;print(sys.version.split()[0])' 2>/dev/null)" "agente/agente.py, ~500 linhas"
ROW "mcp (sdk)"  "$(agente/.venv/bin/python -c 'import importlib.metadata as m;print(m.version("mcp"))' 2>/dev/null)" "2 servidores: mcp-grafana (stdio) + Tempo (HTTP)"
echo
echo "  PALCO"
ROW "doitlive"   "$(doitlive --version 2>/dev/null | grep -o '[0-9][0-9.]*')" "roteiro/demo.sh"
ROW "glow / pandoc" "$(glow --version 2>/dev/null | grep -o '[0-9][0-9.]*') / $(pandoc --version 2>/dev/null | head -1 | grep -o '[0-9][0-9.]*')" "renderiza contexto/*.md"
echo
