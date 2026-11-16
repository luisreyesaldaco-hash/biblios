"""Colapso jerárquico de una nebulosa: galaxias apartadas entre sí, sus estrellas dentro, los fragmentos dentro de su estrella.
Lo usan gen_mapa3d.py (los 52 filósofos) y oradores/gen_platon.py (Platón)."""
import collections, numpy as np

F_EST, F_GAL = 0.07, 0.32   # contracción del fragmento hacia su estrella / de la estrella hacia su galaxia


def separar(c, r, hueco, vueltas=400):
    """Empuja centros c (n×3) hasta que ningún par se traslape (radios r + hueco)."""
    c = c.copy()
    for _ in range(vueltas):
        movio = False
        for a in range(len(c)):
            d = c - c[a]; n = np.linalg.norm(d, axis=1); n[n == 0] = 1e-6
            m = r + r[a] + hueco
            for b in np.where((n < m) & (np.arange(len(c)) > a))[0]:
                empuje = d[b] / n[b] * (m[b] - n[b]) / 2; c[a] -= empuje; c[b] += empuje; movio = True
        if not movio: break
    return c


def galaxia_de_estrellas(P, G, E):
    """Cada estrella pertenece a la galaxia de la mayoría de sus fragmentos (o a la de centro más cercano si ninguno tiene)."""
    G, E = np.asarray(G), np.asarray(E)
    CG = {g: P[G == g].mean(0) for g in set(G.tolist()) if g >= 0}
    out = {}
    for e in sorted(set(E.tolist()) - {-1}):
        cg = collections.Counter(int(g) for g in G[E == e] if g >= 0)
        out[e] = cg.most_common(1)[0][0] if cg else min(CG, key=lambda k: float(np.linalg.norm(CG[k] - P[E == e].mean(0))))
    return out


def colapsar(P, G, E, gal_de=None, hueco_gal=0.22, abrir=1.3, cielo=1.0):
    """Devuelve (Q, gal_de, gal_de_pt): posiciones colapsadas, galaxia de cada estrella, galaxia de cada fragmento."""
    G, E = np.asarray(G), np.asarray(E)
    gal_de = gal_de or galaxia_de_estrellas(P, G, E)
    cE = {e: np.median(P[E == e], 0) for e in gal_de}
    rE = {e: F_EST * float(np.percentile(np.linalg.norm(P[E == e] - cE[e], axis=1), 85)) + 0.006 for e in gal_de}
    GS = sorted(set(gal_de.values()))
    nuevaE, cG0, rG = {}, {}, {}
    for g in GS:
        es = [e for e in gal_de if gal_de[e] == g]
        w = np.array([(E == e).sum() for e in es], float)
        cG0[g] = (np.array([cE[e] for e in es]) * w[:, None]).sum(0) / w.sum()
        o = separar(np.array([(cE[e] - cG0[g]) * F_GAL for e in es]), np.array([rE[e] for e in es]), 0.012)
        o -= (o * w[:, None]).sum(0) / w.sum()
        nuevaE.update(zip(es, o))
        rG[g] = max(float(np.linalg.norm(x)) + rE[e] for e, x in zip(es, o))
    cG1 = dict(zip(GS, separar(np.array([cG0[g] * abrir for g in GS]), np.array([rG[g] for g in GS]), hueco_gal)))
    Q = P.copy()
    gal_de_pt = [gal_de[int(e)] if e >= 0 else int(g) for g, e in zip(G, E)]
    for i in range(len(P)):
        if E[i] >= 0: Q[i] = cG1[gal_de[int(E[i])]] + nuevaE[int(E[i])] + (P[i] - cE[int(E[i])]) * F_EST
        elif G[i] in cG1: Q[i] = cG1[G[i]] + (P[i] - cG0[G[i]]) * F_GAL   # polvo de una galaxia: viaja con ella
    # Encuadre: el cúmulo colapsado ocupa el mismo cielo que la nebulosa difusa.
    mov = np.array([E[i] >= 0 or G[i] in cG1 for i in range(len(P))])
    cen = (Q[mov].max(0) + Q[mov].min(0)) / 2
    esc = min(1.0, cielo * float(np.percentile(np.linalg.norm(P - np.median(P, 0), axis=1), 97)) / float(np.linalg.norm(Q[mov] - cen, axis=1).max()))
    Q[mov] = np.median(P, 0) + (Q[mov] - cen) * esc
    return Q, gal_de, gal_de_pt
