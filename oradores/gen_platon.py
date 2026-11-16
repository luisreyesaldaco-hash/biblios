"""Genera platon.html (página hermana del universo 3D): la nebulosa de Platón con galaxias, estrellas y posturas de Jev."""
import json, re, glob, collections, pathlib, sys, numpy as np
A = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(A.parent / "atlas")); from gravedad import colapsar
U = json.load(open(A / "platon_unidades.json")); R = json.load(open(A / "colapso.json")); X = np.load(A / "platon_3d.npy")
G, E = R["galaxias"]["etiquetas"], R["estrellas"]["etiquetas"]
P = (X - np.median(X, 0)); P /= np.percentile(np.abs(P), 99.5)
limpio = lambda t: re.sub(r"(?m)^[A-Za-z][A-Za-z' ]{0,30}: ", "", t).replace("\n", " ")
pts = [[round(float(P[i, 0]), 4), round(float(P[i, 1]), 4), round(float(P[i, 2]), 4), G[i], E[i], u["dialogo"], u["voz"], limpio(u["texto"])[:200]]
       for i, u in enumerate(U)]
CG = {g: P[[i for i, x in enumerate(G) if x == g]].mean(0) for g in set(G) if g >= 0}
lineas = lambda t: [list(m.groups()) for l in t.split("\n") if (m := re.match(r"([A-Za-z][A-Za-z' ]{0,30}): (.*)", l))]
estrellas = {}
for e, g in R["estrellas"]["grupos"].items():
    idx = [i for i, x in enumerate(E) if x == int(e)]
    cg = collections.Counter(G[i] for i in idx if G[i] >= 0)
    if cg: gal = cg.most_common(1)[0][0]
    else:   # sin fragmentos en ninguna galaxia: la de centro más cercano en el mapa
        c = P[idx].mean(0); gal = min(CG, key=lambda k: float(np.linalg.norm(CG[k] - c)))
    estrellas[e] = {"n": g["n"], "palabras": g["palabras"], "voces": g["voces"], "dialogos": g["dialogos"], "galaxia": gal,
                    "rep": [{"dialogo": U[i]["dialogo"], "lineas": [[o, t[:420]] for o, t in lineas(U[i]["texto"])][:6]} for i in g["rep"]]}
galaxias = {k: {"n": v["n"], "palabras": v["palabras"]} for k, v in R["galaxias"]["grupos"].items()}

# Estado colapsado, por jerarquía (atlas/gravedad.py).
Q, _, gal_de_pt = colapsar(P, G, E, gal_de={int(e): v["galaxia"] for e, v in estrellas.items()})
for i, p in enumerate(pts):
    p[3] = gal_de_pt[i]; p += [round(float(Q[i, 0]), 4), round(float(Q[i, 1]), 4), round(float(Q[i, 2]), 4)]
posturas = {}
for f in glob.glob(str(A / "posturas_*.json")):
    d = json.load(open(f)); I = d["intervenciones"]; citas = []
    for o in sorted(d["tabla"], key=lambda o: -sum(d["tabla"][o].values()))[:3]:
        for k in ("apoya", "contradice"):
            c = sorted([x for x in I if x["orador"] == o and x["postura"] == k], key=lambda x: -x["conf"])
            if c and c[0]["conf"] > 0.8: citas.append({"orador": o, "postura": k, "texto": c[0]["texto"][:260] + "…"})
    posturas[d["estrella"]] = {"proposicion": d["proposicion"], "tabla": d["tabla"], "citas": citas}
datos = {"pts": pts, "galaxias": galaxias, "estrellas": estrellas, "posturas": posturas}
tpl = open(A / "platon_tpl.html", encoding="utf-8").read()
open(A / "platon.html", "w", encoding="utf-8").write(tpl.replace("/*DATOS*/null", json.dumps(datos, ensure_ascii=False, separators=(",", ":"))))
print("platon.html", len(pts), "puntos,", len(estrellas), "estrellas,", len(posturas), "con posturas")
