
# Memória enxuta (regra de economia de contexto)
- Todo `MEMORY.md` entra no contexto de TODA sessão do projeto. Mantenha o índice curto: uma linha por memória, gancho de no máximo ~110 caracteres; o detalhe vai no arquivo da memória, nunca no índice.
- Ao salvar memória nova, se o índice passar de ~40 linhas ou ~6 KB, junte memórias do mesmo assunto ou apague as obsoletas antes de acrescentar.
- Teto de piso: CLAUDE.md global + do projeto + tudo que é `@importado` + MEMORY.md deve ficar em ~15k tokens. Não faça `@import` de arquivo grande (AGENTS.md etc.): deixe normas curtas (~4k) no CLAUDE.md e o resto lido sob demanda. O hook `floor-guard` (SessionStart) avisa quando passar.
- Rotina `~/.claude/bin/memory-diet.py --apply` (timer semanal) encurta ganchos longos; não substitui esta regra.
