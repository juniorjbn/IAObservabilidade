#!/bin/bash
# Um cliente tentando comprar. Repete até ver o erro (ou desiste em 15s).
# Existe porque logo depois de `make incidente` o pool leva uns segundos
# para encher: um curl solto podia voltar sucesso e matar o momento.
for i in $(seq 1 15); do
  saida=$(curl -s -m 5 -w '\n%{http_code}' -X POST localhost:8001/checkout)
  code=${saida##*$'\n'}
  corpo=${saida%$'\n'*}
  printf 'HTTP %s  %s\n' "$code" "$corpo"
  [ "${code:-0}" -ge 500 ] && exit 0
  sleep 1
done
echo "(15s sem erro — o incidente não pegou; rode make incidente de novo)"
exit 1
