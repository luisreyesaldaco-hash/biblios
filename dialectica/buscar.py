"""Fase 2 de la dialéctica (corre en Newton): búsquedas de tesis y antítesis → top-K pasajes por búsqueda (e5, coseno).
Uso: python buscar.py q001.json [--muestra]  → q001_candidatos.json
Por omisión busca en el corpus COMPLETO (completo.json, 36,540 pasajes); --muestra usa los 16,277 del mapa."""
import json, sys, numpy as np, torch
from sentence_transformers import SentenceTransformer
Q = json.load(open(sys.argv[1])); K = 12
MUESTRA = "--muestra" in sys.argv
F = json.load(open("pasajes.json" if MUESTRA else "completo.json"))
V = np.load("vectores.npy" if MUESTRA else "completo_vectores.npy").astype(np.float32)
m = SentenceTransformer("intfloat/multilingual-e5-large", device="mps" if torch.backends.mps.is_available() else "cpu")
qs = [("tesis", q) for q in Q["tesis"]] + [("antitesis", q) for q in Q["antitesis"]] + [("proposicion", Q["proposicion"])]
E = m.encode(["query: " + q for _, q in qs], normalize_embeddings=True)
cand = {}
for (via, q), e in zip(qs, E):
    s = V @ e
    for i in np.argsort(-s)[:K]:
        c = cand.setdefault(int(i), {"i": int(i), "autor": F[i]["autor"], "obra": F[i]["obra"], "pos": F[i]["pos"], "texto": F[i]["texto"], "sim": 0, "vias": []})
        c["sim"] = max(c["sim"], round(float(s[i]), 4)); c["vias"].append(via)
# Además, los K_AUTOR mejores de CADA autor (máximo sobre todas las búsquedas): un autor que trata el tema de pasada
# (Kant y la promesa mentirosa) nunca gana el top global, pero sí debe llegar al clasificador.
K_AUTOR = 4
S = (V @ E.T).max(1); autores = np.array([f["autor"] for f in F])
for a in sorted(set(autores)):
    idx = np.where(autores == a)[0]
    for i in idx[np.argsort(-S[idx])[:K_AUTOR]]:
        c = cand.setdefault(int(i), {"i": int(i), "autor": F[i]["autor"], "obra": F[i]["obra"], "pos": F[i]["pos"], "texto": F[i]["texto"],
                                     "sim": round(float(S[i]), 4), "vias": []})
        c["vias"].append("por_autor")
# Vía léxica (como la búsqueda por palabra clave de legalatlas): TF-IDF de las consultas contra cada pasaje,
# los K_LEX mejores por autor. Atrapa la doctrina dicha con sus palabras aunque el pasaje trate de otra cosa.
from sklearn.feature_extraction.text import TfidfVectorizer
K_LEX = 3
tv = TfidfVectorizer(stop_words="english", sublinear_tf=True, min_df=2)
T = tv.fit_transform([f["texto"] for f in F]); qv = tv.transform([" ".join(Q.get("terminos") or [q for _, q in qs])])   # términos clave del concepto en disputa
L = (T @ qv.T).toarray().ravel()
for a in sorted(set(autores)):
    idx = np.where(autores == a)[0]
    for i in idx[np.argsort(-L[idx])[:K_LEX]]:
        if L[i] <= 0: continue
        c = cand.setdefault(int(i), {"i": int(i), "autor": F[i]["autor"], "obra": F[i]["obra"], "pos": F[i]["pos"], "texto": F[i]["texto"],
                                     "sim": round(float(S[i]), 4), "vias": []})
        c["vias"].append("lexica")
out = sorted(cand.values(), key=lambda c: -c["sim"])
json.dump({"id": Q["id"], "corpus": "muestra" if MUESTRA else "completo", "candidatos": out}, open(Q["id"] + "_candidatos.json", "w"), ensure_ascii=False)
print(len(out), "candidatos únicos de", len(qs), "búsquedas")
