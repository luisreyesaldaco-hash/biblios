"""Divide los diálogos dramáticos de Platón (Jowett, Gutenberg) por orador.
Corta la introducción de Jowett: el diálogo empieza en la última lista 'PERSONS OF THE DIALOGUE'."""
import re, json, sys, pathlib, collections
TXT = pathlib.Path(__file__).resolve().parents[1] / "fuentes/gutenberg/txt"
ROTULO = re.compile(r"^\s*([A-Z][A-Z' ]{1,30}?): (.*)")

def dividir(gid):
    t = (TXT / f"{gid}.txt").read_text(encoding="utf-8", errors="ignore")
    t = t[t.find("*** START"):t.find("*** END")]
    t = t[t.rfind("PERSONS OF THE DIALOGUE"):]           # fuera la introducción del traductor
    personas = t.split("\n\n", 1)[0]
    turnos, actual = [], None
    for linea in t.splitlines()[1:]:
        m = ROTULO.match(linea)
        if m and m.group(1).strip() not in ("SCENE",):
            actual = {"orador": m.group(1).strip().title(), "texto": m.group(2)}
            turnos.append(actual)
        elif actual and linea.strip():
            actual["texto"] += " " + linea.strip()
        elif actual and not linea.strip() and actual["texto"].endswith("\n\n") is False:
            actual["texto"] += "\n"
    return personas, turnos

if __name__ == "__main__":
    for gid in sys.argv[1:]:
        p, T = dividir(gid)
        pal = collections.Counter()
        for x in T: pal[x["orador"]] += len(x["texto"].split())
        print(f"\n== {gid}: {len(T)} turnos | {' '.join(p.split())[:150]}")
        for o, n in pal.most_common(): print(f"   {o:12} {n:6} palabras  {sum(x['orador']==o for x in T):4} turnos")
        json.dump(T, open(pathlib.Path(__file__).parent / f"{gid}_turnos.json", "w"), ensure_ascii=False)
