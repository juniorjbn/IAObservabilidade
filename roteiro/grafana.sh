#!/bin/bash
# Abre o dashboard da demo ("Loja — o incidente", provisionado em lgtm/).
#   roteiro/grafana.sh pool     -> dashboard inteiro: pool, vazão, erro, logs do worker
#   roteiro/grafana.sh worker   -> só o painel de logs do worker, em tela cheia
# Depois de olhar, Cmd+Tab volta pro iTerm.

case "$1" in
  pool)   open 'http://localhost:3000/d/loja-incidente?orgId=1&refresh=5s&from=now-5m&to=now&kiosk' ;;
  worker) open 'http://localhost:3000/d/loja-incidente?orgId=1&refresh=5s&from=now-5m&to=now&viewPanel=4&kiosk' ;;
  *) echo "uso: $0 pool|worker"; exit 1 ;;
esac
