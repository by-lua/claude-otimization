# claude-otimization

Kit pra **gastar menos limite do Claude Code**: medir, cortar peso fixo, reduzir crescimento de contexto, cuidar do cache.
Feito a partir de um setup real e pesado (200+ skills, 12 plugins, dezenas de projetos).

- 📖 [`docs/OTIMIZACAO.md`](docs/OTIMIZACAO.md) — guia completo (o que pesa, como cortar, o kit, como medir)
- 🧭 [`docs/DECISOES.md`](docs/DECISOES.md) — decisões, motivos, como reverter, tabela de alavancas
- 🤖 [`docs/AGENTE.md`](docs/AGENTE.md) — prompt pra colar no **seu** Claude e ele aplicar tudo com confirmação

## Uso rápido

```bash
git clone https://github.com/by-lua/claude-otimization && cd claude-otimization
python3 scripts/token-diet.py          # relatório, não altera nada
./scripts/install.sh                   # dry-run do instalador
./scripts/install.sh --apply           # rotina semanal + deny Agent
./scripts/install.sh --apply --plugins # + context-mode e cache-keepalive (terceiros)
```

Requer `python3` e `jq`; o timer usa `systemd --user` (sem ele, rode o `token-diet.py --apply` de vez em quando).

## O que tem aqui
- `scripts/token-diet.py` — skills sem uso em 30 dias viram `name-only` (reversível); relata agents e memória
- `scripts/install.sh` — instalador com dry-run por padrão
- `systemd/` — timer semanal do token-diet
- `config/settings.snippet.json` — trechos de `settings.json`

Ferramentas de terceiros citadas (rtk, caveman, token-optimizer, context-mode, headroom…) **não** são redistribuídas aqui: só links e status de teste.
Licenças de algumas estão como NOASSERTION no GitHub; confira antes de usar.

## Segurança
Nada aqui lê ou grava credenciais. `install.sh` faz backup do `settings.json` antes de editar. Leia o script antes de rodar.

MIT.
