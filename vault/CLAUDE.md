# Vault — instruções pro Claude Code
Base de conhecimento central (memória persistente entre sessões, estilo Zettelkasten). Método: lucasrosati/claude-code-memory-setup.

## Regras de nota
- Wikilinks `[[nome-da-nota]]`; frontmatter YAML obrigatório (title, tags, created, updated, status, type).
- Arquivos em kebab-case; 1 conceito por nota permanente; mínimo 2 wikilinks por nota.
- Nunca apagar nota sem perguntar. Nunca gravar credenciais/tokens aqui.

## Pastas
permanent/ (notas atômicas) · inbox/ (captura crua) · fleeting/ (temporárias) · logs/ (logs de sessão) · references/ · chats/ · graphify/ (grafos de código)
Por projeto: crie `~/vault/<projeto>/{architecture,pipeline,data,features,logs}` sob demanda.
