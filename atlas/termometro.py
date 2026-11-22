"""Termómetro de estilo: ¿cuánto pesa la VOZ del autor (estilo, traductor) frente al TEMA en los vectores?
Si los vecinos de un pasaje son casi todos del mismo autor, el mapa agrupa voces, no ideas.
Mide antes y después de "centrar" (restar el promedio de cada autor, como colapso_universo.py --centrar).
Corre en DEMIAN (liviano): ~/lab/bench-emb-venv/bin/python termometro.py  -> termometro.json"""
import json, collections, numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.metrics import normalized_mutual_info_score as nmi

F = json.load(open("pasajes.json")); V = np.load("vectores.npy").astype(np.float32); assert len(F) == len(V)
aut = np.array([f["autor"] for f in F]); obra = np.array([f["obra"] for f in F])
K = 15

def centrar(V):
    V = V.copy(); media = V.mean(0)
    for a in set(aut): V[aut == a] += media - V[aut == a].mean(0)
    return V / np.linalg.norm(V, axis=1, keepdims=True)

p = np.array(list(collections.Counter(aut).values())) / len(aut)
azar = float((p ** 2).sum())   # prob. de que un vecino al azar sea del mismo autor

def medir(V, nombre):
    _, ix = NearestNeighbors(n_neighbors=K + 1, metric="cosine").fit(V).kneighbors(V)
    ix = ix[:, 1:]                                             # sin el propio pasaje
    mismo = aut[ix] == aut[:, None]
    misma_obra = obra[ix] == obra[:, None]
    voto = np.array([collections.Counter(aut[r]).most_common(1)[0][0] for r in ix])
    lr = cross_val_score(LogisticRegression(max_iter=300, C=1.0), V, aut, cv=5, n_jobs=2).mean()
    por_autor = {a: float(mismo[aut == a].mean()) for a in sorted(set(aut))}
    r = {"vecinos_mismo_autor": float(mismo.mean()),
         "vecinos_misma_obra_si_mismo_autor": float(misma_obra.sum() / max(1, mismo.sum())),
         "knn_acierta_autor": float((voto == aut).mean()),
         "logistica_acierta_autor": float(lr),
         "por_autor": por_autor}
    print(f"\n== {nombre}\n  vecinos del mismo autor: {r['vecinos_mismo_autor']:.1%}  (azar {azar:.1%})"
          f"\n  kNN adivina el autor:    {r['knn_acierta_autor']:.1%}\n  logística adivina:       {lr:.1%}"
          f"\n  de los vecinos del mismo autor, de la misma obra: {r['vecinos_misma_obra_si_mismo_autor']:.1%}", flush=True)
    return r

res = {"azar": azar, "crudo": medir(V, "crudo"), "centrado": medir(centrar(V), "centrado")}

# ¿Las galaxias del colapso siguen a los autores o a los temas? NMI(galaxia, autor): 1 = cada galaxia es un autor.
for nombre, f in (("colapso crudo", "colapso_universo.json"), ("colapso centrado", "colapso_universo_centrado.json")):
    C = json.load(open(f))
    for nivel in ("galaxias", "estrellas"):
        l = np.array(C[nivel]["etiquetas"]); m = l >= 0
        res[f"nmi_{nombre}_{nivel}"] = float(nmi(aut[m], l[m]))
        print(f"  NMI(autor, {nivel}) {nombre}: {res[f'nmi_{nombre}_{nivel}']:.3f}  ({len(set(l[m]))} grupos)")

print("\nAutores con más 'voz propia' después de centrar (vecinos del mismo autor):")
for a, v in sorted(res["centrado"]["por_autor"].items(), key=lambda x: -x[1])[:12]:
    print(f"  {v:6.1%}  {a}   (crudo {res['crudo']['por_autor'][a]:.1%})")
print("...y los que menos:")
for a, v in sorted(res["centrado"]["por_autor"].items(), key=lambda x: x[1])[:6]:
    print(f"  {v:6.1%}  {a}   (crudo {res['crudo']['por_autor'][a]:.1%})")
json.dump(res, open("termometro.json", "w"), ensure_ascii=False, indent=1)
