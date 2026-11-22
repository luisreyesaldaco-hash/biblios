"""EVōC (TutteInstitute/evoc) frente al colapso actual (UMAP 10D + HDBSCAN + vecinos, colapso_universo.py --centrar).
EVōC agrupa directo sobre los embeddings (1,024D) y da varias escalas de una vez.
Corre en Newton:  .venv-topo/bin/python evoc_comparar.py  -> evoc_capas.npy, evoc_comparar.json"""
import json, time, collections, numpy as np, evoc
from sklearn.metrics import adjusted_rand_score as ari, normalized_mutual_info_score as nmi

F = json.load(open("pasajes.json")); V = np.load("vectores.npy").astype(np.float32); assert len(F) == len(V)
aut = np.array([f["autor"] for f in F])
V = V.copy(); media = V.mean(0)                       # mismo centrado que colapso_universo.py --centrar
for a in set(aut): V[aut == a] += media - V[aut == a].mean(0)
V /= np.linalg.norm(V, axis=1, keepdims=True)
np.save("vectores_centrados.npy", V)

C = json.load(open("colapso_universo_centrado.json"))
ref = {n: np.array(C[n]["etiquetas"]) for n in ("galaxias", "estrellas")}

def describir(l, nombre):
    m = l >= 0
    r = {"grupos": int(len(set(l[m]))), "ruido": float((~m).mean()), "nmi_autor": float(nmi(aut[m], l[m]))}
    for n, R in ref.items():
        b = m & (R >= 0)
        r[f"ari_vs_{n}"] = float(ari(R[b], l[b])); r[f"nmi_vs_{n}"] = float(nmi(R[b], l[b]))
    print(f"  {nombre:12s} {r['grupos']:4d} grupos  polvo {r['ruido']:5.1%}  NMI-autor {r['nmi_autor']:.3f}  "
          f"vs galaxias ARI {r['ari_vs_galaxias']:.2f}/NMI {r['nmi_vs_galaxias']:.2f}  "
          f"vs estrellas ARI {r['ari_vs_estrellas']:.2f}/NMI {r['nmi_vs_estrellas']:.2f}", flush=True)
    return r

res = {"actual": {n: describir(ref[n], f"actual {n[:4]}") for n in ref}}
t = time.time()
import sys
NL = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
modelo = evoc.EVoC(random_state=42, noise_level=NL)
modelo.fit_predict(V)
capas = modelo.cluster_layers_
print(f"EVōC: {len(capas)} capas en {time.time() - t:.0f} s", flush=True)
res["evoc"] = [describir(np.asarray(l), f"evoc capa {i}") for i, l in enumerate(capas)]
np.save(f"evoc_capas_nl{NL}.npy", np.array([np.asarray(l) for l in capas]))

# Para cada capa de EVōC, los 3 autores más presentes en sus 8 grupos más grandes (para leer a ojo).
for i, l in enumerate(capas):
    l = np.asarray(l); tam = collections.Counter(l[l >= 0]).most_common(8)
    res["evoc"][i]["mayores"] = [{"n": n, "autores": collections.Counter(aut[l == c]).most_common(3)} for c, n in tam]
json.dump(res, open(f"evoc_comparar_nl{NL}.json", "w"), ensure_ascii=False, indent=1)
