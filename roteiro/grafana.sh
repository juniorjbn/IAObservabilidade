#!/bin/bash
# Abre o Grafana Explore já com a query certa, para não digitar nada ao vivo.
#   roteiro/grafana.sh pool     -> métrica de pool dos três serviços, últimos 5 min
#   roteiro/grafana.sh worker   -> logs do reconciliation-worker no Loki
# Depois de olhar, Cmd+Tab volta pro iTerm.

case "$1" in
  pool)   open 'http://localhost:3000/explore?schemaVersion=1&orgId=1&panes=%7B%22a%22%3A%7B%22datasource%22%3A%22prometheus%22%2C%22queries%22%3A%5B%7B%22refId%22%3A%22A%22%2C%22expr%22%3A%22db_pool_conexoes_em_uso%22%2C%22legendFormat%22%3A%22%7B%7Bservice_name%7D%7D%22%2C%22datasource%22%3A%7B%22type%22%3A%22prometheus%22%2C%22uid%22%3A%22prometheus%22%7D%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-5m%22%2C%22to%22%3A%22now%22%7D%7D%7D' ;;
  worker) open 'http://localhost:3000/explore?schemaVersion=1&orgId=1&panes=%7B%22a%22%3A%7B%22datasource%22%3A%22loki%22%2C%22queries%22%3A%5B%7B%22refId%22%3A%22A%22%2C%22expr%22%3A%22%7Bservice_name%3D%5C%22reconciliation-worker%5C%22%7D%22%2C%22datasource%22%3A%7B%22type%22%3A%22loki%22%2C%22uid%22%3A%22loki%22%7D%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-15m%22%2C%22to%22%3A%22now%22%7D%7D%7D' ;;
  *) echo "uso: $0 pool|worker"; exit 1 ;;
esac
