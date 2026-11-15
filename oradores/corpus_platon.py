"""Platón completo por orador: dramáticos (rótulos), narrados (reglas + Jev) y la Apología (monólogo).
Salida: platon_turnos.json (un turno por elemento) y platon_unidades.json (ventanas de ~120-260 palabras
para embeber: turnos consecutivos del mismo diálogo, guardando quién dice qué)."""
import json, re, pathlib, collections
from dividir import dividir
from narrados import NARRADOS
from platon_ids import IDS, DUDOSOS
AQUI = pathlib.Path(__file__).resolve().parent
TXT = AQUI.parent / "fuentes/gutenberg/txt"
titulo = lambda g: re.search(r"^Title: (.*)", (TXT / f"{g}.txt").read_text(encoding="utf-8", errors="ignore"), re.M).group(1).strip()

turnos = []
for g in IDS:
    tit = titulo(g)
    if g in NARRADOS:
        T = json.load(open(AQUI / f"{g}_turnos.json"))
    elif g == 1656:   # Apología: Sócrates ante el jurado
        t = (TXT / "1656.txt").read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n")
        t = t[t.find("How you, O Athenians"):t.find("*** END")]
        T = [{"orador": "Socrates", "texto": " ".join(p.split()), "via": "monólogo"} for p in re.split(r"\n\s*\n", t) if p.strip()]
    else:
        _, T = dividir(g)
        for x in T: x["via"] = "rótulo"
    for k, x in enumerate(T):
        o = "narración" if x["orador"] in ("narration", None) else x["orador"]
        turnos.append({"gid": g, "dialogo": tit, "dudoso": g in DUDOSOS, "i": k, "orador": o,
                       "texto": " ".join(x["texto"].split()), "via": x["via"]})

# unidades: ventanas de turnos consecutivos; un turno largo se parte en trozos
unidades, ventana = [], []
def cerrar():
    global ventana
    if ventana and sum(len(t.split()) for _, t in ventana) >= 60:
        pal = collections.Counter()
        for o, t in ventana: pal[o] += len(t.split())
        unidades.append({"gid": g0, "dialogo": d0, "texto": "\n".join(f"{o}: {t}" for o, t in ventana),
                         "voces": dict(pal), "voz": pal.most_common(1)[0][0]})
    ventana = []
prev = None
for x in turnos:
    if prev != x["gid"]: cerrar(); prev = x["gid"]; g0, d0 = x["gid"], x["dialogo"]
    w = x["texto"].split()
    for a in range(0, len(w), 220):
        trozo = " ".join(w[a:a + 220])
        if ventana and sum(len(t.split()) for _, t in ventana) + len(trozo.split()) > 260: cerrar()
        ventana.append((x["orador"], trozo))
        if sum(len(t.split()) for _, t in ventana) >= 120: cerrar()
cerrar()
json.dump(turnos, open(AQUI / "platon_turnos.json", "w"), ensure_ascii=False)
json.dump(unidades, open(AQUI / "platon_unidades.json", "w"), ensure_ascii=False)
pal = collections.Counter()
for x in turnos: pal[x["orador"]] += len(x["texto"].split())
print(f"{len(turnos):,} turnos, {sum(pal.values()):,} palabras, {len(pal)} voces, {len(unidades):,} unidades")
print(", ".join(f"{o} {n:,}" for o, n in pal.most_common(25)))
print("voz principal por unidad:", collections.Counter(u["voz"] for u in unidades).most_common(12))
