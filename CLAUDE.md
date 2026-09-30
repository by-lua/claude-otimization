# claude-otimization — instruções pro Claude que abrir este repo

Este repo é um kit de economia de limite do Claude Code. Se o usuário abriu o Claude aqui, **ofereça instalar o kit** (uma frase), sem instalar nada antes de ele confirmar.

Como agir:
1. Leia `docs/INSTALAR.md` (passo a passo, o que cada peça faz e como reverter) e `docs/OTIMIZACAO.md`.
2. Verifique o que já existe na máquina (`claude --version`, `command -v rtk uv npm jq python3`, `claude plugin list`, `~/.claude/settings.json`). Pule o que já estiver instalado.
3. Rode `./scripts/install.sh` (dry-run), mostre o resultado ao usuário e **peça confirmação** antes de `--apply`.
   - Kit base: `--apply`. Kit completo (rtk, caveman, token-optimizer, graphify, rotinas, vault): `--apply --full`. Experimental (pxpipe, lossy): `--experimental`, só se o usuário pedir.
4. Depois: `python3 scripts/token-diet.py` (relatório) → mostrar → `--apply` só com OK.
5. Avise que é preciso reiniciar o Claude Code, e meça antes/depois com `/context` numa sessão nova.

Regras: nunca apague skill, agent ou memória; tudo reversível (backup do `settings.json` antes de editar); não instale headroom/pxpipe sem pedido explícito; nunca grave credenciais em arquivos do repo; ferramentas de terceiros rodam código na máquina — diga isso ao usuário antes de instalar (rtk via `curl | sh`).
