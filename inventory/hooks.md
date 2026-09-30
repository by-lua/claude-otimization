# Hooks (evento -> script; argumentos omitidos)

## CwdChanged
- `*` -> python-launcher.sh

## PostCompact
- `*` -> python-launcher.sh

## PostToolUse
- `Bash|Read|Glob|Grep|Agent|mcp__.*` -> python-launcher.sh
- `Bash|Read|Grep|Glob|mcp__.*` -> python-launcher.sh
- `Edit|Write|MultiEdit|NotebookEdit` -> python-launcher.sh
- `Bash|Read|Glob|Grep|Agent|Edit|Write|MultiEdit|NotebookEdit|mcp__.*` -> python-launcher.sh

## PreCompact
- `*` -> python-launcher.sh
- `*` -> python-launcher.sh
- `*` -> python-launcher.sh
- `*` -> auto-handoff.py

## PreToolUse
- `Read` -> python-launcher.sh
- `Bash` -> python-launcher.sh
- `Agent|Task` -> python-launcher.sh
- `Bash` -> pretool_secret_guard.py
- `Bash` -> pretool_capi_test_guard.py

## SessionEnd
- `*` -> python-launcher.sh
- `*` -> auto-handoff.py

## SessionStart
- `*` -> python-launcher.sh
- `*` -> python-launcher.sh
- `*` -> python-launcher.sh
- `*` -> claude-fanout.sh
- `compact` -> python-launcher.sh
- `*` -> session-start-notice.py

## Stop
- `*` -> python-launcher.sh
- `*` -> python-launcher.sh
- `*` -> python-launcher.sh

## StopFailure
- `*` -> python-launcher.sh

## UserPromptSubmit
- `*` -> measure.py
- `*` -> python-launcher.sh
