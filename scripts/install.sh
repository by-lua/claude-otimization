#!/usr/bin/env bash
# claude-otimization — instalador. Nada é apagado; tudo é reversível (ver docs/OTIMIZACAO.md).
#
#   ./scripts/install.sh              # mostra o que faria (dry-run)
#   ./scripts/install.sh --apply      # instala o kit base (diet + timer + deny Agent)
#   ./scripts/install.sh --apply --plugins   # também instala context-mode e cache-keepalive
#   ./scripts/install.sh --apply --no-deny-agent   # não desliga subagents
set -euo pipefail

APPLY=0; PLUGINS=0; DENY_AGENT=1
for a in "$@"; do
  case "$a" in
    --apply) APPLY=1 ;;
    --plugins) PLUGINS=1 ;;
    --no-deny-agent) DENY_AGENT=0 ;;
    *) echo "flag desconhecida: $a"; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")/.." && pwd)"
CL="$HOME/.claude"
run() { if [ "$APPLY" = 1 ]; then echo "+ $*"; "$@"; else echo "[dry-run] $*"; fi; }

command -v python3 >/dev/null || { echo "precisa de python3"; exit 1; }
command -v jq >/dev/null || { echo "precisa de jq"; exit 1; }
mkdir -p "$CL/bin"

# 1) rotina token-diet
run install -m 755 "$HERE/scripts/token-diet.py" "$CL/bin/token-diet.py"

# 2) timer semanal (systemd --user); sem systemd, rode `token-diet.py --apply` à mão de vez em quando
if command -v systemctl >/dev/null && systemctl --user show-environment >/dev/null 2>&1; then
  run mkdir -p "$HOME/.config/systemd/user"
  run install -m 644 "$HERE/systemd/token-diet.service" "$HERE/systemd/token-diet.timer" "$HOME/.config/systemd/user/"
  run systemctl --user daemon-reload
  run systemctl --user enable --now token-diet.timer
else
  echo "systemd --user indisponível: pulei o timer."
fi

# 3) desligar subagents (permissions.deny: Agent) — remove a lista de agents do contexto
if [ "$DENY_AGENT" = 1 ]; then
  if [ "$APPLY" = 1 ]; then
    [ -f "$CL/settings.json" ] || echo '{}' > "$CL/settings.json"
    cp "$CL/settings.json" "$CL/settings.json.bak-otimization"
    jq '.permissions.deny=((.permissions.deny//[])+["Agent"]|unique)' "$CL/settings.json" > "$CL/settings.json.tmp"
    mv "$CL/settings.json.tmp" "$CL/settings.json"; chmod 600 "$CL/settings.json"
    echo "+ permissions.deny += Agent (backup: settings.json.bak-otimization)"
  else
    echo "[dry-run] permissions.deny += Agent"
  fi
fi

# 4) plugins opcionais (terceiros — leia docs/DECISOES.md antes)
if [ "$PLUGINS" = 1 ]; then
  run claude plugin marketplace add mksglu/context-mode
  run claude plugin install context-mode@context-mode
  run claude plugin marketplace add demouo/claude-code-cache-keepalive
  run claude plugin install cache-keepalive@claude-cache-tools
fi

echo
echo "Próximo passo: python3 $CL/bin/token-diet.py   (relatório)   e depois   --apply"
echo "Reinicie o Claude Code pra valer."
