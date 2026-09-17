# Método de investigação — a ordem de quem está de plantão às 2h

Siga NESTA ordem. Use as ferramentas que tiver.

1. **Confirme o sintoma e delimite o raio.** Erros 503 no checkout-api:
   veja nos logs (Loki, label `service_name`) QUEM devolve o erro original —
   o serviço que alerta raramente é o que causa. As mensagens de log são em
   português; não filtre por "error", olhe as linhas.
2. **Saúde dos pools no caminho.** Prometheus: `db_pool_conexoes_em_uso`
   contra `db_pool_capacidade`, por `service_name`. Pool cravado na
   capacidade = conexões presas, quase sempre esperando lock ou query lenta.
3. **Quem mais escreve no mesmo banco?** Consulte o mapa do ambiente. Não
   esqueça processos fora do caminho da requisição (workers, jobs, crons):
   eles não aparecem em trace nenhum. Para cada um, leia os logs dele no
   Loki (`{service_name="<nome>"}`).
4. **Locks agora.** Se não tiver ferramenta para `pg_stat_activity`, os logs
   do processo suspeito costumam dizer o que ele está fazendo com o banco
   (transações longas, backfill, locks).
5. **O que mudou?** Procure nos logs linhas de "mudança de configuração",
   deploy ou flag. Incidente novo quase sempre tem mudança recente por trás.
6. **Com os passos 1 a 5 respondidos, conclua.** Nomeie o componente
   causador e a evidência que o liga ao sintoma. "O serviço X está lento"
   não é causa raiz; "o processo Y segura locks na tabela Z por causa da
   mudança W" é.
