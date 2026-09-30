# Instalar (pra você ou pro seu Claude)

**Jeito mais fácil:** abra o Claude Code dentro da pasta deste repo e diga *"instala o kit de otimização"*. O `CLAUDE.md` da raiz já instrui o Claude a checar o que falta, mostrar o dry-run e pedir sua confirmação.

**Manual:**
```bash
git clone https://github.com/by-lua/claude-otimization && cd claude-otimization
./scripts/install.sh                      # dry-run (não altera nada)
./scripts/install.sh --apply              # base: token-diet + timer semanal + deny Agent
./scripts/install.sh --apply --full       # completo (abaixo)
./scripts/install.sh --apply --experimental   # + pxpipe
```
Requisitos: `claude`, `python3`, `jq`. Para o completo: `curl`, `uv` (graphify), e `npm` só pro pxpipe. Timers usam `systemd --user`; sem systemd, rode os scripts à mão de vez em quando.

## O que cada nível instala

| Nível | Peça | Como (comando que o script roda) |
|---|---|---|
| base | token-diet (skills sem uso → name-only) | copia `scripts/token-diet.py` + timer semanal |
| base | desligar subagents | `permissions.deny += ["Agent"]` (backup do settings) |
| `--plugins` | context-mode | `claude plugin marketplace add mksglu/context-mode` → `claude plugin install context-mode@context-mode` |
| `--plugins` | cache-keepalive | `claude plugin marketplace add demouo/claude-code-cache-keepalive` → `claude plugin install cache-keepalive@claude-cache-tools` |
| `--full` | rtk | `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh \| sh` → `rtk init -g` |
| `--full` | caveman | `claude plugin marketplace add JuliusBrussee/caveman` → `claude plugin install caveman@caveman` |
| `--full` | token-optimizer | `claude plugin marketplace add alexgreensh/token-optimizer` → `claude plugin install token-optimizer@alexgreensh-token-optimizer` |
| `--full` | graphify | `uv tool install graphifyy` |
| `--full` | memory-diet + regra de memória enxuta | copia script, timer e trecho pro `CLAUDE.md` global |
| `--full` | vault + `/vault-save`, `/vault-resume` | cria `~/vault` mínimo |
| `--experimental` | pxpipe | `npm install -g --prefix ~/.local pxpipe-proxy`; use com `claude-px` só em sessão de teste |
| manual | headroom | `uv tool install --python 3.13 "headroom-ai[all]"` (pesado; compare com rtk antes) |

Todos os comandos vêm dos READMEs oficiais de cada projeto (conferidos em 2026-09-30). Confira licenças: caveman, token-optimizer e context-mode aparecem como NOASSERTION no GitHub.

## Segurança e reversão
- Ferramentas de terceiros executam código na sua máquina (o rtk instala via `curl | sh`): leia antes de aceitar.
- Cada mudança em `settings.json` tem backup (`.bak-otimization`, `.bak-diet`). Como desfazer cada item: `docs/DECISOES.md`.
- `otimization-sync.py` publica um inventário no repo de **quem rodar**; ele não vem ativado (edite `REPO` e `ACCOUNT` primeiro) e aborta se o scan achar segredo.

## Depois de instalar
1. Reinicie o Claude Code.
2. `python3 ~/.claude/bin/token-diet.py` → relatório → `--apply`.
3. `/context` numa sessão nova: compare o peso fixo com o de antes.
