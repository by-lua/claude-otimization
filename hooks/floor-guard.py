#!/usr/bin/env python3
"""floor-guard — SessionStart global. Mede o "piso" de contexto que a sessao paga antes da 1a mensagem
(CLAUDE.md global + do projeto + @imports + MEMORY.md) e, se passar do teto, manda o Claude avisar
o usuario e propor o enxugamento. Nao edita nada sozinho (arquivo de projeto e decisao do dono).

Teto: FLOOR_CEILING_TOKENS (padrao 15000) para instrucoes+memoria; FLOOR_REAL_TOKENS (padrao 70000)
para o piso REAL medido na ultima sessao do mesmo projeto. Falha aberta: erro nunca bloqueia a sessao.
"""
import hashlib, json, os, re, sys, glob, time

CEIL = int(os.environ.get("FLOOR_CEILING_TOKENS", 15000))
CEIL_REAL = int(os.environ.get("FLOOR_REAL_TOKENS", 70000))
HOME = os.path.expanduser("~")
IMP = re.compile(r"(?<![\w`@/])@((?:~|\.{1,2})?/?[\w.\-/]+\.\w+)")


def tok(n_chars):
    return int(n_chars / 3.5)


def read(p):
    try:
        return open(p, errors="ignore").read()
    except Exception:
        return None


def imports(path, text, seen, depth=0):
    out = []
    if depth > 4:
        return out
    fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        for m in IMP.finditer(line):
            rel = m.group(1)
            p = os.path.expanduser(rel) if rel.startswith("~") else os.path.normpath(os.path.join(os.path.dirname(path), rel))
            if p in seen or not os.path.isfile(p):
                continue
            seen.add(p)
            t = read(p)
            if t is not None:
                out.append((p, t))
                out += imports(p, t, seen, depth + 1)
    return out


def collect(cwd):
    files, seen = [], set()
    cands = [f"{HOME}/.claude/CLAUDE.md"]
    d = os.path.abspath(cwd)
    chain = []
    while True:
        chain.append(d)
        if d == "/" or d == os.path.dirname(d):
            break
        d = os.path.dirname(d)
    for d in reversed(chain):
        cands += [f"{d}/CLAUDE.md", f"{d}/CLAUDE.local.md", f"{d}/.claude/CLAUDE.md"]
    slug = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(cwd))
    cands.append(f"{HOME}/.claude/projects/{slug}/memory/MEMORY.md")
    for p in cands:
        if p in seen or not os.path.isfile(p):
            continue
        seen.add(p)
        t = read(p)
        if t is None:
            continue
        files.append((p, t))
        files += imports(p, t, seen)
    return files, slug


def dupes(files):
    seen, waste, ex = {}, 0, []
    for p, t in files:
        for blk in re.split(r"\n\s*\n", t):
            b = re.sub(r"\s+", " ", blk).strip()
            if len(b) < 250:
                continue
            h = hashlib.md5(b.encode()).hexdigest()
            if h in seen:
                waste += len(b)
                ex.append(b[:50])
            else:
                seen[h] = p
    return tok(waste), ex[:3]


def real_floor(slug):
    fs = sorted(glob.glob(f"{HOME}/.claude/projects/{slug}/*.jsonl"), key=os.path.getmtime, reverse=True)
    for f in fs[:2]:
        try:
            with open(f, errors="ignore") as fh:
                for i, line in enumerate(fh):
                    if i > 400:
                        break
                    if '"usage"' in line and '"assistant"' in line:
                        j = json.loads(line)
                        m = j.get("message") or {}
                        u = m.get("usage") or {}
                        if m.get("model", "").startswith("<") or j.get("isSidechain"):
                            continue
                        return u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        except Exception:
            continue
    return None


def main():
    try:
        ev = json.load(sys.stdin)
    except Exception:
        ev = {}
    cwd = ev.get("cwd") or os.getcwd()
    files, slug = collect(cwd)
    total = sum(tok(len(t)) for _, t in files)
    rf = real_floor(slug)
    dup_tok, dup_ex = dupes(files)
    try:
        os.makedirs(f"{HOME}/.claude/token-diet", exist_ok=True)
        with open(f"{HOME}/.claude/token-diet/floor.jsonl", "a") as lf:
            lf.write(json.dumps({"t": time.strftime("%F %T"), "cwd": cwd, "instr_tok": total, "real_floor": rf, "dup_tok": dup_tok}) + "\n")
    except Exception:
        pass
    over_instr = total > CEIL
    over_real = rf is not None and rf > CEIL_REAL
    if not (over_instr or over_real or dup_tok > 1500):
        return
    top = sorted(((tok(len(t)), p) for p, t in files), reverse=True)[:4]
    tops = "; ".join(f"{p.replace(HOME, '~')} ({n//1000}k)" for n, p in top if n > 500)
    parts = []
    if over_instr:
        parts.append(f"instrucoes+memoria carregadas: ~{total//1000}k tokens (teto {CEIL//1000}k). Maiores: {tops}")
    if over_real:
        parts.append(f"piso real da ultima sessao deste projeto: {rf//1000}k tokens antes da 1a mensagem (teto {CEIL_REAL//1000}k)")
    if dup_tok > 1500:
        parts.append(f"~{dup_tok//1000}k tokens em blocos DUPLICADOS entre os arquivos carregados (ex.: '{dup_ex[0]}...')")
    acoes = []
    if over_instr or dup_tok > 1500:
        acoes.append("(1) CLAUDE.md do projeto so com normas curtas (~4k) e o resto sob demanda em arquivo lido quando preciso, sem @import do arquivo grande; (2) remover blocos duplicados; (3) enxugar o MEMORY.md (juntar/apagar)")
    if over_real and not over_instr:
        acoes.append("o peso vem de skills/plugins/MCP, nao dos arquivos de instrucao: rode `python3 ~/.claude/bin/token-diet.py` (relatorio) e sugira desativar plugins/MCPs que este projeto nao usa")
    msg = ("[floor-guard] Piso de contexto acima do teto: " + " | ".join(parts) + ". "
           "ACAO: na sua primeira resposta, avise o usuario em 1-2 linhas e ofereca: " + "; ".join(acoes) + ". "
           "NAO edite sem OK do usuario e nao interrompa uma tarefa urgente dele.")
    print(json.dumps({
        "systemMessage": f"floor-guard: piso ~{total//1000}k tok (teto {CEIL//1000}k)" + (f", real {rf//1000}k" if rf else ""),
        "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg},
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
