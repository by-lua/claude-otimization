#!/usr/bin/env bash
# self-update — mantém a sua cópia do claude-otimization em dia. Roda pelo timer diário (systemd --user).
# Faz `git pull --ff-only` e, se veio algo novo, reinstala só scripts/hooks/units (--refresh).
# NÃO reinstala plugins nem mexe em settings.json (isso só o install.sh --apply, com você presente).
# Se você editou arquivos do clone e o pull não é fast-forward, ele PULA e registra no log.
set -uo pipefail
CL="$HOME/.claude"; LOG="$CL/token-diet/update.log"; mkdir -p "$CL/token-diet"
REPO="${OTIMIZATION_REPO_DIR:-$(cat "$CL/token-diet/repo-path" 2>/dev/null || true)}"
log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }
[ -n "$REPO" ] && [ -d "$REPO/.git" ] || { log "repo nao encontrado (rode install.sh de novo)"; exit 0; }
cd "$REPO"
git fetch -q origin 2>>"$LOG" || { log "fetch falhou (sem rede?)"; exit 0; }
LOCAL=$(git rev-parse HEAD); REMOTE=$(git rev-parse '@{u}' 2>/dev/null || git rev-parse origin/main)
[ "$LOCAL" = "$REMOTE" ] && { log "em dia ($(git rev-parse --short HEAD))"; exit 0; }
if git merge-base --is-ancestor "$LOCAL" "$REMOTE"; then
  git pull -q --ff-only 2>>"$LOG" || { log "pull falhou"; exit 0; }
  log "atualizado $(git rev-parse --short "$LOCAL") -> $(git rev-parse --short HEAD)"
  bash "$REPO/scripts/install.sh" --apply --refresh >>"$LOG" 2>&1 && log "refresh ok" || log "refresh falhou"
else
  log "clone divergente (alteracoes locais?): pulei. Resolva com git status."
fi
