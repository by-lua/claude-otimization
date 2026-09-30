#!/usr/bin/env python3
"""token-diet — rotina de economia de contexto do Claude Code.

Todo skill/agent/plugin ativo paga descricao no contexto de TODA sessao (e o cache
relê isso em toda chamada). Este script mede o que foi usado nos ultimos N dias
(lendo os transcripts locais) e enxuga o resto, de forma reversivel.

  token-diet.py                 # relatorio (dry-run, nao altera nada)
  token-diet.py --apply         # aplica: skills sem uso -> name-only; volta as que voltaram a ser usadas
  token-diet.py --apply --agents  # tambem arquiva agents sem uso em ~/.claude/agents-disabled/
  token-diet.py --days 45       # janela de uso (padrao 30)

Nunca apaga nada. Skills ganham "name-only" em settings.json (skillOverrides);
o script so mexe nas chaves que ele mesmo criou (estado em ~/.claude/token-diet/state.json).
"""
import argparse, glob, json, os, re, shutil, time, collections

CL = os.path.expanduser("~/.claude")
SETTINGS = f"{CL}/settings.json"
STATE_DIR = f"{CL}/token-diet"
STATE = f"{STATE_DIR}/state.json"

# sempre completas, mesmo sem uso recente (ajuste pro seu setup)
PROTECT_SKILLS = {"graphify", "humanizer", "resumo-sessao", "caveman", "token-optimizer",
                  "find-skills", "skill-creator", "update-config"}
# agents que apps externos (Overclock etc.) podem referenciar: nunca arquivar
PROTECT_AGENT_PREFIX = ("overclock-", "qa-", ".")


def usage(days):
    """conta Skill/slash-command e subagent_type usados nos transcripts."""
    cutoff = time.time() - days * 86400
    sk, ag = collections.Counter(), collections.Counter()
    for f in glob.glob(f"{CL}/projects/**/*.jsonl", recursive=True):
        try:
            if os.path.getmtime(f) < cutoff:
                continue
        except OSError:
            continue
        for line in open(f, errors="ignore"):
            if '"Skill"' in line or '"Agent"' in line or '"Task"' in line:
                for m in re.finditer(r'"name":"(Skill|Agent|Task)","input":\{([^}]*)\}', line):
                    inp = m.group(2)
                    if m.group(1) == "Skill":
                        s = re.search(r'"skill":"([^"]+)"', inp)
                        if s:
                            sk[s.group(1)] += 1
                    else:
                        s = re.search(r'"subagent_type":"([^"]+)"', inp)
                        if s:
                            ag[s.group(1)] += 1
            if "<command-name>" in line:
                for m in re.finditer(r"<command-name>/?([^<]+)</command-name>", line):
                    sk[m.group(1).strip()] += 1
    return sk, ag


def installed_skills():
    names = set()
    for p in glob.glob(f"{CL}/skills/*"):
        if os.path.isdir(p) or os.path.islink(p):
            names.add(os.path.basename(p))
    return names


def load(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--agents", action="store_true")
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()

    sk, ag = usage(a.days)
    used = set(sk) | {k.split(":")[-1] for k in sk}
    settings = load(SETTINGS, {})
    ov = settings.get("skillOverrides", {})
    state = load(STATE, {"managed": []})
    managed = set(state["managed"])

    skills = installed_skills()
    to_trim = sorted(s for s in skills if s not in used and s not in PROTECT_SKILLS and ov.get(s) != "name-only")
    to_restore = sorted(s for s in managed if s in used and ov.get(s) == "name-only")

    print(f"janela: {a.days}d | skills instaladas: {len(skills)} | usadas: {len(used & skills)} | ja name-only: {sum(1 for v in ov.values() if v == 'name-only')}")
    print(f"-> passar a name-only ({len(to_trim)}): {', '.join(to_trim[:60])}{' ...' if len(to_trim) > 60 else ''}")
    print(f"-> voltar a completa ({len(to_restore)}): {', '.join(to_restore)}")

    agents_dir = f"{CL}/agents"
    agents = [f[:-3] for f in os.listdir(agents_dir) if f.endswith(".md")] if os.path.isdir(agents_dir) else []
    unused_agents = sorted(x for x in agents if x not in ag and not x.startswith(PROTECT_AGENT_PREFIX))
    kb = sum(os.path.getsize(f"{agents_dir}/{x}.md") for x in unused_agents) // 1024
    print(f"agents: {len(agents)} | sem uso em {a.days}d: {len(unused_agents)} (~{kb} KB) {'-> arquivar' if a.agents else '(use --agents pra arquivar)'}")
    if "Agent" in settings.get("permissions", {}).get("deny", []):
        print("   (Agent esta em permissions.deny: a lista de agents nem entra no contexto)")

    # auditoria de memoria / CLAUDE.md (so relatorio: editar isso e decisao humana)
    for label, p in (("MEMORY.md", glob.glob(f"{CL}/projects/*/memory/MEMORY.md")), ("CLAUDE.md global", [f"{CL}/CLAUDE.md"])):
        for f in p:
            if os.path.exists(f):
                txt = open(f).read()
                longs = [l for l in txt.splitlines() if len(l) > 180]
                print(f"{label}: {len(txt)//1024} KB (~{len(txt)//4} tok), {len(longs)} linhas >180 chars  [{os.path.relpath(f, CL)}]")

    if not a.apply:
        print("\n(dry-run) nada alterado. Rode com --apply.")
        return

    shutil.copy(SETTINGS, f"{SETTINGS}.bak-diet")
    for s in to_trim:
        ov[s] = "name-only"
        managed.add(s)
    for s in to_restore:
        ov.pop(s, None)
        managed.discard(s)
    settings["skillOverrides"] = ov
    tmp = SETTINGS + ".tmp"
    json.dump(settings, open(tmp, "w"), indent=2, ensure_ascii=False)
    os.replace(tmp, SETTINGS)
    os.chmod(SETTINGS, 0o600)

    if a.agents:
        dst = f"{CL}/agents-disabled"
        os.makedirs(dst, exist_ok=True)
        for x in unused_agents:
            shutil.move(f"{agents_dir}/{x}.md", f"{dst}/{x}.md")
        print(f"agents arquivados: {len(unused_agents)} -> {dst}")

    os.makedirs(STATE_DIR, exist_ok=True)
    state["managed"] = sorted(managed)
    state["last_run"] = time.strftime("%Y-%m-%d %H:%M")
    json.dump(state, open(STATE, "w"), indent=2)
    print("aplicado. Reinicie a sessao pra valer. Backup: settings.json.bak-diet")


if __name__ == "__main__":
    main()
