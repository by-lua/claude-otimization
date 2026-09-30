# Prompt pro seu Claude aplicar isso (cole no Claude Code)

> Leia `docs/OTIMIZACAO.md` e `docs/DECISOES.md` deste repositório e otimize o meu Claude Code, nesta ordem:
> 1. Meça: rode `python3 scripts/token-diet.py` (relatório) e me mostre o resultado. Peça `/context` numa sessão nova e anote os tokens.
> 2. Faça backup de `~/.claude/settings.json`.
> 3. Rode `./scripts/install.sh` (dry-run), mostre o que vai fazer e **peça minha confirmação** antes de `--apply`.
> 4. Sugira (sem aplicar) quais plugins/MCPs eu quase não uso e podem sair do escopo global.
> 5. Só depois, se eu pedir, instale os plugins de teste (`--plugins`) e compare antes/depois.
> Regras: nunca apague skill, agent ou memória; tudo tem de ser reversível; não instale proxies (headroom/pxpipe) sem eu pedir; não escreva credenciais em nenhum arquivo do repo.
