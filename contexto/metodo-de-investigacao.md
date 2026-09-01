# Método de investigação — a ordem de quem está de plantão às 2h

Siga NESTA ordem. Cada passo tem uma ferramenta preferida.

1. **Confirme o sintoma e delimite o raio.** Erros 503 no checkout-api:
   veja nos logs (`query_loki_logs`, label `service_name`) QUEM devolve o
   erro original — o serviço que alerta raramente é o que causa.
2. **Saúde dos pools no caminho.** Use `saude_do_pool`. Pool cravado na
   capacidade com esgotamentos subindo = conexões presas, quase sempre
   esperando lock ou query lenta.
3. **Quem mais escreve no mesmo banco?** Consulte o mapa do ambiente. Não
   esqueça processos fora do caminho da requisição (workers, jobs, crons):
   eles não aparecem em trace nenhum.
4. **Locks agora.** Use `quem_esta_segurando_locks`. Se alguém segura lock
   há muitos segundos com transação aberta, esse é o principal suspeito.
5. **O que mudou?** Use `mudancas_recentes`. Incidente novo quase sempre
   tem mudança recente por trás — deploy, flag, config.
6. **Com os passos 1 a 5 respondidos, conclua IMEDIATAMENTE.** Não busque
   confirmação extra em traces: workers e jobs sem HTTP não geram trace, e
   ausência deles lá não prova nada. Nomeie o componente causador e a
   evidência que o liga ao sintoma. "O serviço X está lento" não é causa
   raiz; "o processo Y segura locks na tabela Z há N segundos por causa da
   mudança W" é.
