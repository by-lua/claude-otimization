#!/usr/bin/env python3
"""memory-diet — mantém os MEMORY.md (indices de memoria do Claude Code) enxutos.

O MEMORY.md inteiro entra no contexto de TODA sessao do projeto. Cada memoria ja tem o
detalhe no proprio arquivo, entao a linha do indice so precisa de titulo + gancho curto.

  memory-diet.py            # relatorio
  memory-diet.py --apply    # encurta ganchos > --max chars (padrao 110), com backup .bak-diet

So mexe em linhas no formato  "- [Titulo](arquivo.md) — gancho". Nada some: o texto completo
esta no arquivo da memoria. Linhas fora desse formato nao sao tocadas.
"""
import argparse, glob, os, re, shutil

CL = os.path.expanduser("~/.claude")
LINE = re.compile(r"^(- \[[^\]]+\]\([^)]+\)) [—-] (.*)$")


def shorten(hook, mx):
    if len(hook) <= mx:
        return hook
    cut = hook[:mx].rsplit(" ", 1)[0].rstrip(" ,;:.-—(")
    return cut + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--max", type=int, default=110)
    ap.add_argument("--threshold", type=int, default=5000, help="so mexe em MEMORY.md maior que isso (bytes)")
    a = ap.parse_args()
    tot_before = tot_after = 0
    for f in sorted(glob.glob(f"{CL}/projects/*/memory/MEMORY.md")):
        txt = open(f).read()
        if len(txt.encode()) <= a.threshold:
            continue
        out, changed = [], 0
        for l in txt.splitlines():
            m = LINE.match(l)
            if m and len(m.group(2)) > a.max:
                l = f"{m.group(1)} — {shorten(m.group(2), a.max)}"
                changed += 1
            out.append(l)
        new = "\n".join(out) + ("\n" if txt.endswith("\n") else "")
        b, n = len(txt.encode()), len(new.encode())
        tot_before += b; tot_after += n
        print(f"{b//1024:>3} KB -> {n//1024:>3} KB  ({changed} linhas)  {os.path.basename(os.path.dirname(os.path.dirname(f)))[-60:]}")
        if a.apply and changed:
            shutil.copy(f, f + ".bak-diet")
            open(f, "w").write(new)
    print(f"total: {tot_before//1024} KB -> {tot_after//1024} KB (~{(tot_before-tot_after)//4} tokens por sessao somados)")
    if not a.apply:
        print("(dry-run) use --apply")


if __name__ == "__main__":
    main()
