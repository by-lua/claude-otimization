#!/usr/bin/env python3
"""otimization-sync — espelha o setup de otimização do Claude Code no repo público claude-otimization.

Varre a config local (plugins, MCPs, hooks, settings, skills, rotinas), gera um INVENTARIO
sanitizado em inventory/, copia scripts/timers/comandos genericos, roda scan de segredos e,
se estiver limpo, faz commit + push.

  otimization-sync.py            # gera + scan, NAO commita (dry-run)
  otimization-sync.py --push     # gera + scan + commit + push (conta by-lua via gh)

O que NUNCA sai: conteudo de skills proprias, env/headers/args de MCP, memorias, transcripts,
credenciais, nomes de projetos/clientes. Skills proprias entram so como contagem.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time

CL = os.path.expanduser("~/.claude")
HOME = os.path.expanduser("~")
REPO = os.path.expanduser(os.environ.get("OTIMIZATION_REPO", "~/Projetos/claude-otimization"))
ACCOUNT = "by-lua"

SECRET_RES = [
    r"gh[pousr]_[A-Za-z0-9]{20,}", r"sk-[A-Za-z0-9_-]{16,}", r"AKIA[0-9A-Z]{12,}", r"xox[abprs]-[A-Za-z0-9-]{10,}",
    r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}", r"-----BEGIN [A-Z ]*PRIVATE KEY",
    r"[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com|noreply\.anthropic\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b(?!127\.0\.0\.1|0\.0\.0\.0)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    r"/home/[a-z][a-z0-9_-]*/", r"(?i)(api[_-]?key|secret|passw(or)?d|senha|token)\s*[:=]\s*['\"]?[A-Za-z0-9/+_-]{12,}",
]


def load(p, d):
    try:
        return json.load(open(os.path.expanduser(p)))
    except Exception:
        return d


def w(rel, text):
    p = os.path.join(REPO, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(text.replace(HOME, "~"))


def inv_plugins(st):
    en = [k for k, v in st.get("enabledPlugins", {}).items() if v]
    mk = st.get("extraKnownMarketplaces", {})
    rows = ["| Plugin | Marketplace (repo) |", "|---|---|"]
    for k in sorted(en):
        name, _, m = k.partition("@")
        src = (mk.get(m, {}).get("source", {}) or {})
        repo = src.get("repo") or ("(oficial/desconhecido)" if not src else "(url)")
        rows.append(f"| {name} | {repo} |")
    return f"# Plugins ativos ({len(en)})\n\n" + "\n".join(rows) + "\n"


def inv_mcp(cj):
    rows = ["| MCP | Tipo | Comando |", "|---|---|---|"]
    for k, v in sorted((cj.get("mcpServers") or {}).items()):
        cmd = os.path.basename(v.get("command", "")) if v.get("command") else "(remoto)"
        rows.append(f"| {k} | {v.get('type', 'stdio')} | {cmd} |")
    return "# MCP servers globais (so nome/tipo; env, args e URLs ficam de fora)\n\n" + "\n".join(rows) + "\n"


def inv_hooks(st):
    out = ["# Hooks (evento -> script; argumentos omitidos)\n"]
    for ev, blocks in sorted((st.get("hooks") or {}).items()):
        items = []
        for b in blocks:
            for h in b.get("hooks", []):
                c = h.get("command", "")
                m = re.findall(r"[\w./-]+\.(?:py|sh)", c)
                items.append((b.get("matcher", "*"), os.path.basename(m[0]) if m else c.split()[0][:40]))
        out.append(f"## {ev}\n" + "\n".join(f"- `{mt}` -> {s}" for mt, s in items) + "\n")
    return "\n".join(out)


def inv_settings(st):
    keep = {
        "model": st.get("model"), "effortLevel": st.get("effortLevel"),
        "permissions": {"deny": (st.get("permissions") or {}).get("deny", [])},
        "env_keys": sorted((st.get("env") or {}).keys()),
        "skillOverrides_count": len(st.get("skillOverrides") or {}),
        "hook_events": sorted((st.get("hooks") or {}).keys()),
    }
    return json.dumps(keep, indent=2, ensure_ascii=False) + "\n"


def inv_skills(st):
    n = len([p for p in glob.glob(f"{CL}/skills/*") if os.path.isdir(p) or os.path.islink(p)])
    ov = st.get("skillOverrides") or {}
    state = load(f"{CL}/token-diet/state.json", {})
    return (f"# Skills (contagem; conteudo nao e publicado)\n\n- instaladas: {n}\n- em name-only: {sum(1 for v in ov.values() if v == 'name-only')}\n"
            f"- gerenciadas pelo token-diet: {len(state.get('managed', []))}\n- ultima rodada do token-diet: {state.get('last_run', '-')}\n")


def inv_routines():
    rows = ["| Timer | Agenda |", "|---|---|"]
    for t in ("claude-sync", "token-diet", "memory-diet", "otimization-sync"):
        p = os.path.expanduser(f"~/.config/systemd/user/{t}.timer")
        if os.path.exists(p):
            cal = re.search(r"OnCalendar=(.*)", open(p).read())
            rows.append(f"| {t} | {cal.group(1) if cal else '?'} |")
    return "# Rotinas automaticas (systemd --user)\n\n" + "\n".join(rows) + "\n"


def copy_generic():
    for src, dst in (
        (f"{CL}/bin/token-diet.py", "scripts/token-diet.py"),
        (f"{CL}/bin/memory-diet.py", "scripts/memory-diet.py"),
        (f"{CL}/bin/otimization-sync.py", "scripts/otimization-sync.py"),
        (f"{CL}/bin/claude-px", "scripts/claude-px"),
        (f"{CL}/hooks/economia/floor-guard.py", "hooks/floor-guard.py"),
        (f"{CL}/commands/vault-save.md", "vault/commands/vault-save.md"),
        (f"{CL}/commands/vault-resume.md", "vault/commands/vault-resume.md"),
        (os.path.expanduser("~/vault/CLAUDE.md"), "vault/CLAUDE.md"),
        (os.path.expanduser("~/vault/templates/default-note.md"), "vault/templates/default-note.md"),
    ):
        if os.path.exists(src):
            os.makedirs(os.path.dirname(os.path.join(REPO, dst)), exist_ok=True)
            shutil.copy(src, os.path.join(REPO, dst))
    for t in ("token-diet", "memory-diet", "otimization-sync"):
        for ext in ("service", "timer"):
            s = os.path.expanduser(f"~/.config/systemd/user/{t}.{ext}")
            if os.path.exists(s):
                d = os.path.join(REPO, "systemd", f"{t}.{ext}")
                os.makedirs(os.path.dirname(d), exist_ok=True)
                open(d, "w").write(open(s).read().replace(HOME, "%h"))


def scan():
    hits = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            p = os.path.join(root, f)
            try:
                txt = open(p, errors="ignore").read()
            except Exception:
                continue
            for rx in SECRET_RES:
                for m in re.finditer(rx, txt):
                    line = txt.count("\n", 0, m.start()) + 1
                    # o proprio scanner e os docs listam os padroes; ignora este arquivo
                    if f == "otimization-sync.py":
                        continue
                    hits.append((os.path.relpath(p, REPO), line, rx[:28]))
    return hits


def sh(*a, env=None):
    return subprocess.run(a, cwd=REPO, capture_output=True, text=True, env=env)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    if not os.path.isdir(os.path.join(REPO, ".git")):
        sys.exit(f"repo nao encontrado: {REPO}")
    st = load(f"{CL}/settings.json", {})
    cj = load("~/.claude.json", {})
    w("inventory/plugins.md", inv_plugins(st))
    w("inventory/mcp.md", inv_mcp(cj))
    w("inventory/hooks.md", inv_hooks(st))
    w("inventory/settings.sanitized.json", inv_settings(st))
    w("inventory/skills.md", inv_skills(st))
    w("inventory/rotinas.md", inv_routines())
    copy_generic()
    hits = scan()
    if hits:
        print("SCAN DE SEGREDOS ENCONTROU ITENS — abortando sem commit:")
        for h in hits[:30]:
            print("  ", h)
        sys.exit(3)
    print("scan limpo.")
    if not a.push:
        print("(dry-run) use --push pra commitar e subir.")
        return
    sh("git", "add", "-A")
    if not sh("git", "status", "--porcelain").stdout.strip():
        print("nada mudou.")
        return
    msg = (f"chore(inventory): snapshot {time.strftime('%Y-%m-%d')} de plugins, skills, MCPs e rotinas\n\n"
           "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
    r = sh("git", "-c", f"user.name={ACCOUNT}", "-c", f"user.email={ACCOUNT}@users.noreply.github.com", "commit", "-q", "-m", msg)
    print(r.stdout + r.stderr)
    tok = subprocess.run(["gh", "auth", "token", "-u", ACCOUNT], capture_output=True, text=True).stdout.strip()
    env = dict(os.environ, GH_TOKEN=tok)
    r = sh("git", "push", "-q", "origin", "main", env=env)
    print(r.stdout + r.stderr or "push ok")


if __name__ == "__main__":
    main()
