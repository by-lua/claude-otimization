#!/usr/bin/env bash
# claude-otimization — instalador. Nada é apagado; tudo é reversível (ver docs/OTIMIZACAO.md).
#
#   ./scripts/install.sh              # mostra o que faria (dry-run)
#   ./scripts/install.sh --apply      # instala o kit base (diet + timer + deny Agent)
#   ./scripts/install.sh --apply --plugins   # também instala context-mode e cache-keepalive
#   ./scripts/install.sh --apply --full      # kit completo: + rtk, caveman, token-optimizer, graphify, memory-diet, vault, sync do repo
#   ./scripts/install.sh --apply --experimental   # + pxpipe (lossy, sessão isolada). headroom fica manual (ver docs/INSTALAR.md)
#   ./scripts/install.sh --apply --no-deny-agent   # não desliga subagents
set -euo pipefail

APPLY=0; PLUGINS=0; DENY_AGENT=1; FULL=0; EXPERIMENTAL=0
for a in "$@"; do
  case "$a" in
    --apply) APPLY=1 ;;
    --plugins) PLUGINS=1 ;;
    --full) FULL=1; PLUGINS=1 ;;
    --experimental) EXPERIMENTAL=1 ;;
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

have() { command -v "$1" >/dev/null 2>&1; }

# 5) kit completo: ferramentas de terceiros (cada uma é pulada se já estiver instalada)
if [ "$FULL" = 1 ]; then
  have claude || { echo "precisa do Claude Code (claude) instalado"; exit 1; }
  if have rtk; then echo "rtk já instalado"; else
    run bash -c 'curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh'
  fi
  have rtk && run rtk init -g          # registra o hook no Claude Code
  run claude plugin marketplace add JuliusBrussee/caveman
  run claude plugin install caveman@caveman
  run claude plugin marketplace add alexgreensh/token-optimizer
  run claude plugin install token-optimizer@alexgreensh-token-optimizer
  if have uv; then run uv tool install graphifyy; else echo "sem uv: pulei o graphify (instale uv e rode: uv tool install graphifyy)"; fi

  # rotinas próprias
  run install -m 755 "$HERE/scripts/memory-diet.py" "$CL/bin/memory-diet.py"
  run install -m 755 "$HERE/scripts/otimization-sync.py" "$CL/bin/otimization-sync.py"
  run install -m 755 "$HERE/scripts/claude-px" "$CL/bin/claude-px"
  if command -v systemctl >/dev/null && systemctl --user show-environment >/dev/null 2>&1; then
    run install -m 644 "$HERE/systemd/memory-diet.service" "$HERE/systemd/memory-diet.timer" "$HOME/.config/systemd/user/"
    run systemctl --user daemon-reload
    run systemctl --user enable --now memory-diet.timer
    echo "otimization-sync (publica inventário no SEU repo) NÃO é ativado aqui: edite REPO/ACCOUNT no script primeiro."
  fi

  # vault mínimo (método claude-code-memory-setup)
  run mkdir -p "$HOME/vault"/{permanent,inbox,fleeting,templates,logs,references,chats/code,graphify} "$CL/commands"
  [ -f "$HOME/vault/CLAUDE.md" ] || run cp "$HERE/vault/CLAUDE.md" "$HOME/vault/CLAUDE.md"
  run cp -n "$HERE/vault/templates/default-note.md" "$HOME/vault/templates/default-note.md"
  run cp -n "$HERE/vault/commands/vault-save.md" "$HERE/vault/commands/vault-resume.md" "$CL/commands/"

  # regra de memória enxuta no CLAUDE.md global (só se ainda não estiver)
  if [ "$APPLY" = 1 ] && ! grep -q "Memória enxuta" "$CL/CLAUDE.md" 2>/dev/null; then
    cat "$HERE/config/claude-md-memoria-enxuta.md" >> "$CL/CLAUDE.md"; echo "+ regra de memória enxuta em CLAUDE.md"
  fi
fi

if [ "$EXPERIMENTAL" = 1 ]; then
  have npm && run npm install -g --prefix "$HOME/.local" pxpipe-proxy || echo "sem npm: pulei o pxpipe"
fi

echo
echo "Próximo passo: python3 $CL/bin/token-diet.py   (relatório)   e depois   --apply"
echo "Reinicie o Claude Code pra valer."
