# Otimização de contexto, cache e tokens no Claude Code

Guia prático, medido em um setup real pesado (200+ skills, 12 plugins, dezenas de projetos, sessões de horas).
Serve pra você ler, ou pra colar no seu Claude e mandar ele aplicar (veja `AGENTE.md`).

> Regra de ouro: **meça antes de instalar qualquer coisa**. Quase sempre o maior custo é o peso fixo de cada sessão, não falta de ferramenta.

## 1. Como o limite é consumido (o modelo mental)

- Toda chamada reenvia o contexto inteiro. O **cache** faz isso custar ~10x menos, mas ainda conta.
- Portanto: `custo ≈ (tamanho do contexto) × (número de chamadas)`.
- Dois botões: **encolher o contexto** (peso fixo + crescimento) e **reduzir chamadas** (tool calls, subagents, loops).
- O cache expira (5 min ou 1 h conforme o plano). Sessão parada e retomada depois relê tudo "a frio", mais caro.

Medido (mediana de 210 sessões em 3 dias): **~85k tokens de contexto antes de digitar a primeira mensagem**.
Sessões longas chegaram a 410–658k de contexto com 500–930 chamadas (uma leu 373M de tokens só de cache).

## 2. Onde está o peso fixo (e como cortar)

| Fonte | Medido | Corte | Risco |
|---|---|---|---|
| Descrições de skills | 203 skills ≈ 66 KB (~17k tokens) | `skillOverrides: name-only` nas que você não usa (rotina `token-diet`) | Baixo: a skill continua chamável por nome/slash |
| Lista de agents/subagents | 48 agents ≈ 300 KB de arquivos | `permissions.deny: ["Agent"]` remove a ferramenta (e a lista) do contexto | Perde delegação a subagent |
| Plugins | 12 ativos, vários de nicho | Desativar por projeto (`enabledPlugins` no `settings.local.json` do projeto) | Baixo |
| Hooks que injetam texto | vários por sessão/prompt | Revisar `settings.json`; cada `additionalContext` custa em toda sessão/prompt | Médio (depende do hook) |
| `CLAUDE.md` global + memória | ~14 KB + ~8 KB | Mover seções raras pra arquivo lido sob demanda (deixar 2–3 linhas + ponteiro) | Baixo |
| MCP servers | cada tool = schema no contexto | Remover os que não usa; preferir CLI | Baixo |

Comandos úteis: `/context` (mostra o que ocupa a janela), `/usage`, `/compact`, `/clear`.

## 3. Reduzir o crescimento durante a sessão

1. **Saída de comandos** (`git`, `ls`, testes, logs) é o que mais infla. Use um proxy/filtro (`rtk`) e/ou sandbox de tool output (`context-mode`).
2. **Compacte cedo**: `/compact` perto de 150k, ou `/clear` entre tarefas. Um handoff automático (`resumo-sessao`) torna o `/clear` barato.
3. **Leia menos arquivo inteiro**: grafo do código (`graphify`) em vez de reler o projeto toda sessão.
4. **Modelo certo por tarefa**: Sonnet como padrão, Opus só pra decisão difícil; `effortLevel` baixo por padrão.
5. **Subagents/paralelismo**: cada um relê o próprio contexto e consome o mesmo limite. Menos workers, fechar os ociosos.

## 4. Cache

- Mantenha o **prefixo estável**: não mexa em CLAUDE.md/skills/hooks no meio da sessão (invalida o cache).
- **cache-keepalive**: hook + Monitor que faz um ping barato quando a sessão fica ociosa, mantendo o cache quente. Vale só se você **volta** às sessões; em sessão abandonada vira gasto puro. Limite com `CCKA_MAX_IDLE_SECONDS`.
- `CLAUDE_CODE_PROMPT_CACHE_TTL=1h` (quando aplicável ao seu plano/API) reduz recriação de cache.

## 5. O kit (o que já usamos + o que estamos testando)

Legenda: ✅ em uso e aprovado · 🧪 em teste · ⛔ descartado/só sandbox · 👀 candidato ainda não testado.

| Peça | Repo | Função | Status |
|---|---|---|---|
| **rtk** (Rust Token Killer) | `rtk-ai/rtk` | Proxy de CLI que comprime saída de comandos via hook (60–90% em operações de dev) | ✅ |
| **caveman** | `JuliusBrussee/caveman` | Modo de resposta comprimida (menos tokens de saída). Licença NOASSERTION, confira | ✅ |
| **token-optimizer** | `alexgreensh/token-optimizer` | Hooks que arquivam tool results, cacheiam leituras e medem qualidade/sessão. Licença NOASSERTION | ✅ |
| **resumo-sessao** | (skill própria) | Handoff automático no PreCompact/SessionEnd e reinjeção no SessionStart. Tem custo (gera resumo em background): desligar com `touch ~/.claude/session-handoffs/OFF` | ✅ opcional |
| **token-diet** | este repo | Rotina que põe skills sem uso em `name-only` e volta as que voltaram a ser usadas | ✅ |
| `permissions.deny: Agent` | config | Desliga subagents | ✅ |
| **context-mode** | `mksglu/context-mode` | MCP + hooks: tool output vai pra sandbox/SQLite, só o resumo entra no contexto | 🧪 |
| **cache-keepalive** | `demouo/claude-code-cache-keepalive` | Ping em sessão ociosa pra manter o cache | 🧪 |
| **headroom** | `headroomlabs-ai/headroom` | Proxy/wrap que comprime tool outputs, logs e histórico; overlap com rtk | 🧪 (comparar com rtk antes de empilhar) |
| **pxpipe** | `teamchong/pxpipe` | Proxy que renderiza contexto volumoso como imagem. **Lossy**: IDs/hashes podem ser lidos errado em silêncio | ⛔ só sessão descartável |
| **ccusage** | `ccusage/ccusage` | Custo/tokens por dia, sessão, bloco de 5h (lê os JSONL locais) | 👀 |
| **claude-pace / usage-bar** | `Astro-Han/claude-pace`, `leeguooooo/claude-code-usage-bar` | Statusline com uso 5h/7d e ritmo de consumo | 👀 |
| **claude-hud** | `jarrodwatts/claude-hud` | Statusline com contexto, agents, todos | 👀 |
| **houtini-lm** | `houtini-ai/houtini-lm` | MCP que delega tarefa barata a LLM local/OpenRouter | 👀 |
| **graphify** | (skill) | Projeto vira grafo de conhecimento: Claude consulta o grafo em vez de reler arquivos | ✅ nos projetos grandes |
| **claude-mem** | `thedotmack/claude-mem` | Memória persistente entre sessões (captura observações, resume, reinjeta) | 👀 |
| **claude-code-memory-setup** | `lucasrosati/claude-code-memory-setup` | Guia Obsidian + Graphify (alega 71,5x menos tokens/sessão, número do autor, não verificado) | 👀 |

Nota sobre conflito: `rtk`, `context-mode` e `headroom` mexem em saída de tools/requests. Empilhar sem medir pode duplicar
ou brigar (dois hooks reescrevendo `Bash`). Ative um por vez e compare.

## 6. Rotinas automáticas

| Rotina | Frequência | O que faz |
|---|---|---|
| `token-diet.py --apply` (systemd timer) | semanal | Skills sem uso em 30 dias → `name-only`; as que voltaram → completa |
| `claude-sync.sh push` (opcional) | diária | Espelha config do Claude (sem credenciais) numa pasta sincronizada |
| `/compact` ou `/clear` | por tarefa | Manual, mas com o handoff automático fica barato |

`token-diet` não apaga nada; só mexe nas chaves que ele mesmo criou e guarda backup do `settings.json`.

## 6b. Guarda automática contra inchaço (floor-guard)

`hooks/floor-guard.py` roda em todo início de sessão. Soma `CLAUDE.md` global + da árvore do projeto + tudo que é `@importado`
+ `MEMORY.md` e compara com um teto. Estourou → o Claude avisa e oferece o corte. Padrão que funciona: `CLAUDE.md` do projeto com
só as normas curtas (~4k) e o resto num arquivo lido sob demanda (uma linha no `CLAUDE.md` dizendo *quando* ler), em vez de
`@AGENTS.md` importando 30k+ em toda sessão.

## 7. Como medir (antes/depois)

1. `/context` numa sessão nova, sem digitar nada: anote os tokens de "System prompt", "Skills", "MCP tools", "Memory files".
2. Aplique **uma** mudança, reinicie, meça de novo.
3. Consumo real: `npx ccusage` (por dia/bloco) ou some `usage` dos JSONL em `~/.claude/projects`.
4. Para proxies (headroom/pxpipe): rode a **mesma tarefa** com e sem, compare tokens e **confira o resultado** (não só o custo).

## 8. Erros comuns

- Instalar 5 ferramentas de compressão ao mesmo tempo e não saber qual ajudou.
- Deixar sessão de 500k aberta "porque está no meio". Compacte/`/clear` + handoff.
- Ping de cache em sessão que ninguém vai retomar.
- Confiar em proxy lossy pra dado byte-exato (IDs, hashes, tokens, comandos).
- Achar que "name-only" apaga a skill: ela continua chamável, só perde a descrição de auto-trigger.
