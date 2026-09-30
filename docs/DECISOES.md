# Decisões e tabela de otimização

Registro do que foi decidido, por quê, e como reverter. Datas em AAAA-MM-DD. Números medidos no setup do autor.

## Contexto do problema (2026-09-30)
Limite semanal/5h estourando bem mais que o normal. Medição dos transcripts (~210 sessões, 3 dias):
- mediana de **85k tokens** de contexto antes da primeira mensagem;
- sessões de trabalho longas com 400–650k de contexto e 500–900 chamadas;
- 9–10 mil chamadas/dia em Sonnet nos dias piores, com 1,6–2,1 bilhões de tokens lidos de cache por dia.
Conclusão: o problema era **peso fixo + sessões gigantes**, não falta de ferramenta.

## Decisões

| # | Decisão | Motivo | Reverter |
|---|---|---|---|
| D1 | `permissions.deny: ["Agent"]` | Subagents relêem contexto próprio e consomem o mesmo limite; negar a ferramenta também tira a lista de agents (~300 KB de definições) do contexto | remover `"Agent"` de `permissions.deny` |
| D2 | Rotina `token-diet` semanal (skills sem uso em 30d → `name-only`) | 203 skills ≈ 17k tokens só de descrição; 110 sem uso no mês | `python3 token-diet.py` só relata; para desfazer restaure `settings.json.bak-diet` ou apague as chaves de `skillOverrides` listadas em `~/.claude/token-diet/state.json` |
| D3 | Desligar handoff automático (`resumo-sessao`) com `touch ~/.claude/session-handoffs/OFF` | Gera resumo em background a cada compactação/`/clear` e reinjeta texto no início de toda sessão; custo recorrente | `rm ~/.claude/session-handoffs/OFF` |
| D4 | Instalar **context-mode** para teste | Ataca crescimento por tool output (98% de redução alegada, medir) | `claude plugin uninstall context-mode@context-mode` |
| D5 | Instalar **cache-keepalive** para teste | Evita reescrever cache após pausa; risco: ping em sessão abandonada | `claude plugin uninstall cache-keepalive@claude-cache-tools` ou `CCKA_ENABLED=0` |
| D6 | **headroom**: testar só comparando com rtk | Overlap com rtk (ambos comprimem tool output) | `headroom unwrap claude` |
| D7 | **pxpipe**: só sessão descartável | Lossy (IDs/hashes podem sair errados em silêncio), reescreve todo request e passa a credencial por proxy local | não instalar globalmente |
| D8 | Sync automático da config (systemd timer diário) | O `claude-sync.sh` era manual: última cópia tinha semanas | `systemctl --user disable --now claude-sync.timer` |

## Ainda por decidir / testar
- headroom vs rtk: rodar a mesma tarefa com cada um, comparar tokens **e** resultado.
- context-mode junto com rtk: ver se os dois hooks de `Bash` brigam (`/context-mode:ctx-doctor`, `rtk gain`).
- claude-mem (memória persistente) e graphify + Obsidian: úteis em projetos grandes; ver se compensam o custo de captura.
- MEMORY.md por projeto: alguns passam de 10 KB (~3–4k tokens em toda sessão do projeto). Enxugar à mão: manter só regras/decisões vivas, mover o resto pra arquivos de referência.

## Tabela de otimização (o que puxa cada alavanca)

| Alavanca | Ganho esperado | Esforço | Risco | Onde |
|---|---|---|---|---|
| skills → name-only | ~10–15k tokens/sessão | baixo (automático) | baixo | token-diet |
| deny Agent | tira lista de agents + para delegação | 1 linha | perde subagents | settings.json |
| plugins de nicho fora do global | 1–5k tokens/plugin | baixo | baixo | enabledPlugins por projeto |
| MEMORY.md/CLAUDE.md enxutos | 1–4k tokens/sessão | médio (manual) | baixo | arquivos |
| filtro de saída (rtk) | 60–90% nas saídas de CLI | baixo | baixo | hook |
| sandbox de tool output (context-mode) | alto em MCP/Playwright (a medir) | médio | médio | plugin |
| /compact, /clear cedo | evita 400k+ | hábito | baixo | manual |
| Sonnet padrão, Opus sob demanda | ~5x no custo por token | hábito | qualidade em tarefa difícil | `/model` |
| cache-keepalive | 2x em retomadas após pausa | baixo | gasto em sessão abandonada | plugin |
