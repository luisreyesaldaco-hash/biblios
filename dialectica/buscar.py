"""Fase 2 de la dialéctica (corre en Newton): búsquedas de tesis y antítesis → top-K pasajes por búsqueda (e5, coseno).
Uso: python buscar.py q001.json  → q001_candidatos.json"""
import json, sys, numpy as np, torch
from sentence_transformers import SentenceTransformer
Q = json.load(open(sys.argv[1])); K = 12
F = json.load(open("pasajes.json")); V = np.load("vectores.npy")
m = SentenceTransformer("intfloat/multilingual-e5-large", device="mps" if torch.backends.mps.is_available() else "cpu")
qs = [("tesis", q) for q in Q["tesis"]] + [("antitesis", q) for q in Q["antitesis"]] + [("proposicion", Q["proposicion"])]
E = m.encode(["query: " + q for _, q in qs], normalize_embeddings=True)
cand = {}
for (via, q), e in zip(qs, E):
    s = V @ e
    for i in np.argsort(-s)[:K]:
        c = cand.setdefault(int(i), {"i": int(i), "autor": F[i]["autor"], "obra": F[i]["obra"], "texto": F[i]["texto"], "sim": 0, "vias": []})
        c["sim"] = max(c["sim"], round(float(s[i]), 4)); c["vias"].append(via)
out = sorted(cand.values(), key=lambda c: -c["sim"])
json.dump({"id": Q["id"], "candidatos": out}, open(Q["id"] + "_candidatos.json", "w"), ensure_ascii=False)
print(len(out), "candidatos únicos de", len(qs), "búsquedas")
