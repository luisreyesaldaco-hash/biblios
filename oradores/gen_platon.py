"""Genera platon.html (página hermana del universo 3D): la nebulosa de Platón con galaxias, estrellas y posturas de Jev."""
import json, re, glob, collections, pathlib, numpy as np
A = pathlib.Path(__file__).resolve().parent
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

# Estado colapsado, por jerarquía: galaxias separadas entre sí, sus estrellas dentro, los fragmentos dentro de su estrella.
def separar(c, r, hueco, vueltas=400):
    """Empuja centros c (n×3) hasta que ningún par se traslape (radios r + hueco)."""
    c = c.copy()
    for _ in range(vueltas):
        movio = False
        for a in range(len(c)):
            for b in range(a + 1, len(c)):
                d = c[b] - c[a]; n = float(np.linalg.norm(d)) or 1e-6; m = r[a] + r[b] + hueco
                if n < m:
                    empuje = d / n * (m - n) / 2; c[a] -= empuje; c[b] += empuje; movio = True
        if not movio: break
    return c
F_EST, F_GAL = 0.07, 0.32          # contracción del fragmento hacia su estrella / de la estrella hacia su galaxia
Eid = {int(e): v for e, v in estrellas.items()}
gal_de_pt = [Eid[E[i]]["galaxia"] if E[i] >= 0 else G[i] for i in range(len(U))]   # el fragmento toma la galaxia de su estrella
cE = {e: np.median(P[[i for i, x in enumerate(E) if x == e]], 0) for e in Eid}
rE = {e: F_EST * float(np.percentile(np.linalg.norm(P[[i for i, x in enumerate(E) if x == e]] - cE[e], axis=1), 85)) + 0.006 for e in Eid}
GS = sorted({v["galaxia"] for v in Eid.values()})
nuevaE, cG0, rG = {}, {}, {}
for g in GS:
    es = [e for e in Eid if Eid[e]["galaxia"] == g]
    w = np.array([Eid[e]["n"] for e in es], float)
    cG0[g] = (np.array([cE[e] for e in es]) * w[:, None]).sum(0) / w.sum()
    o = separar(np.array([(cE[e] - cG0[g]) * F_GAL for e in es]), np.array([rE[e] for e in es]), 0.012)
    o -= (o * w[:, None]).sum(0) / w.sum()
    for e, x in zip(es, o): nuevaE[e] = x
    rG[g] = max(float(np.linalg.norm(x)) + rE[e] for e, x in zip(es, o))
cG1 = dict(zip(GS, separar(np.array([cG0[g] * 1.3 for g in GS]), np.array([rG[g] for g in GS]), 0.22)))
Q = P.copy()
for i in range(len(U)):
    if E[i] >= 0:
        g = Eid[E[i]]["galaxia"]; Q[i] = cG1[g] + nuevaE[E[i]] + (P[i] - cE[E[i]]) * F_EST
    elif G[i] in cG1:   # polvo de una galaxia: viaja con ella, sin estrella
        Q[i] = cG1[G[i]] + (P[i] - cG0[G[i]]) * F_GAL
# Encuadre: el cúmulo colapsado ocupa el mismo cielo que la nebulosa difusa.
mov = np.array([E[i] >= 0 or G[i] in cG1 for i in range(len(U))])
cen = (Q[mov].max(0) + Q[mov].min(0)) / 2
esc = min(1.0, float(np.percentile(np.linalg.norm(P - np.median(P, 0), axis=1), 97)) / float(np.linalg.norm(Q[mov] - cen, axis=1).max()))
Q[mov] = np.median(P, 0) + (Q[mov] - cen) * esc
print(f"encuadre: escala {esc:.2f}")
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
