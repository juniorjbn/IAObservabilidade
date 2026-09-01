# Roteiro de palco — 30 minutos

Minutagem construída sobre tempos MEDIDOS na calibração (não estimados):
investigação da rodada 1 no 14b: 31–77s de modelo; rodada 2: 27–91s.
Carga fria do 14b: ~37s — por isso o pré-aquecimento é inegociável.

## Antes de subir (na sala, 30 min antes)

```bash
make verificar               # ~70s; NÃO suba ao palco se falhar
make curar                   # garante estado limpo
curl -s http://localhost:11434/api/generate -d \
  '{"model":"qwen3:14b","prompt":"ok","stream":false}' >/dev/null  # pré-aquece
```

- [ ] Grafana aberto na aba do Explore (pool metric, refresh 5s, janela 5min)
- [ ] Terminal 1: fonte grande, pronto com `make incidente`
- [ ] Terminal 2: pronto com `make agente` (rodada 1)
- [ ] Vídeo do plano B acessível offline (não em aba do navegador)
- [ ] Wi-Fi pode cair a qualquer momento: nada depende dele
- [ ] Notificações do macOS em Não Perturbe

## Minutagem

| Quando | Bloco | O que acontece |
|---|---|---|
| 00:00–02:30 | **Abertura** | A promessa do fornecedor ("IA resolve sozinha") vs a ligação às 2h. "Ela não sabe nem o nome dos seus serviços." Tese em uma frase: o gap não é conhecer Kubernetes, é conhecer o SEU. |
| 02:30–05:00 | **O gap tem nome** | Gartner aposentou "AIOps Platforms" (03/2025). Thoughtworks: sem engenharia de contexto, vira chat sobre dados quebrados. Uma frase cada, slide único. |
| 05:00–08:00 | **O ambiente** | Topologia na tela — SEM mostrar o worker no diagrama (ele aparece só na autópsia). Stack local, nada sai da máquina = argumento de ambiente regulado. Mostrar o comando do MCP com `-disable-write` e falar do portão humano. |
| 08:00–09:00 | **O incidente** | `make incidente` ao vivo. Grafana: pool do inventory crava em 5, vazão despenca. "Isso é um plantão de verdade: 503 pro cliente, gráfico feio." |
| 09:00–13:00 | **RODADA 1 — o erro** | `make agente`. Narrar os portões (Enter visível). Modelo leva ~45–80s no total; preencher com leitura das tool calls em voz alta. Diagnóstico: culpa o inventory-api. **Pausa. "Quem concorda com ele?"** Deixar a sala responder. |
| 13:00–16:00 | **Autópsia** | O dado existia DESDE O INÍCIO: mostrar no Grafana o pool metric e os logs do worker (que o agente nunca consultou — não sabia que existiam). Revelar o worker no diagrama. "Não é burrice do modelo. É o que qualquer plantonista novo faria sem contexto." |
| 16:00–17:00 | **A injeção** | `cat contexto/mapa-do-ambiente.md` e `metodo-de-investigacao.md` na tela, rolagem rápida. "Quatro coisas: mapa, método, ferramentas de domínio, mudanças recentes. Zero RAG, zero fine-tuning, zero modelo novo." |
| 17:00–21:00 | **RODADA 2 — o acerto** | `make agente-r2`. Os portões agora mostram `saude_do_pool`, `quem_esta_segurando_locks`, `mudancas_recentes`. Diagnóstico nomeia o worker, a flag e os locks. `make curar`, gráfico volta ao vivo. |
| 21:00–23:00 | **Kicker (cortável)** | Slide: as baterias de calibração. "Isso foi o 14b. O 8b — metade do tamanho — também acerta com contexto: 9 de 10. Sem contexto, o mesmo 8b: zero de dez." Não foi o modelo que cresceu. |
| 23:00–26:30 | **O que isso custa** | PACE-LM: "pesquisadores da Microsoft construíram um estimador de confiança porque o modelo não sabe quando não sabe" (calibração, ~1/3 do erro). Roy et al.: ferramenta bate documento. Engenharia de contexto ≠ RAG. Humano no portão não é enfeite: é o design. |
| 26:30–27:30 | **Fechamento** | Três frases, sem slide: (1) A IA não resolveu o incidente. (2) Quem aprovou cada passo dela, e quem reverte a configuração, é você. (3) O que ela entregou foi o detalhe que você não tinha visto — um worker que não aparece em nenhum trace. |
| 27:30–30:00 | **Q&A** | Respostas hostis prontas no dossiê (`referencias/DOSSIE.md`). |

## Pontos de corte (se atrasar)

1. **Kicker do 8b** (21:00) — 2 min. Corta inteiro, não encolhe.
2. **Referências** (23:00) — de 3,5 min para 1,5: só PACE-LM.
3. NUNCA cortar: autópsia (13:00) — sem ela o antes/depois vira mágica.

## Plano B por modo de falha

| Se... | Então... |
|---|---|
| `make verificar` falhar antes | não há palestra ao vivo: vídeo do início ao fim, assumido de cara ("gravei ontem, e explico por quê ao vivo") |
| modelo travar/vagar na rodada 1 | o teto de 8 passos + conclusão forçada seguram (medido: sempre conclui); se ainda assim sair ruim, "olha aí: nem errar direito ele erra sem contexto" e corta pro vídeo da rodada 1 |
| modelo citar o worker na rodada 1 | nunca aconteceu em ~100 execuções; se acontecer: "hoje ele me traiu acertando — normalmente..." e mostra o slide das baterias |
| rodada 2 vagar | pedir de novo ao vivo custa ~60s ("roda de novo, ao vivo é assim") — 10/10 na calibração diz que a segunda vai |
| Grafana não abrir / projetor 4:3 | tudo que importa está no terminal; Grafana é ilustração |

## Pendências desta etapa

- [ ] Gravar o vídeo do plano B (rodadas 1 e 2 completas, tela limpa)
- [ ] Ensaio completo cronometrado ×2 (a minutagem acima é hipótese até o ensaio)
- [ ] Decidir slide de abertura/identidade visual (fora do escopo deste repo até agora)
