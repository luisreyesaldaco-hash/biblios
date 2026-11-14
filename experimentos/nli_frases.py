import json, re, numpy as np, torch
from sentence_transformers import SentenceTransformer, CrossEncoder
dev = "mps" if torch.backends.mps.is_available() else "cpu"
nli = CrossEncoder("cross-encoder/nli-deberta-v3-large", device=dev)
emb = SentenceTransformer("intfloat/multilingual-e5-large", device=dev)
F = json.load(open("pasajes.json")); V = np.load("vectores.npy")
H = "The mind has innate ideas that do not come from the senses or experience."
q = emb.encode(["query: " + H], normalize_embeddings=True)[0]
esperado = {"Platón":"SÍ","Descartes":"SÍ","Leibniz":"SÍ","Locke":"NO","Hume":"NO","Berkeley":"NO","Kant":"mixto"}
for autor in esperado:
    idx = [i for i, f in enumerate(F) if f["autor"] == autor]
    top = sorted(idx, key=lambda i: -float(V[i] @ q))[:25]
    frases = [(s.strip(), F[i]["obra"]) for i in top for s in re.split(r"(?<=[.;?!])\s+", F[i]["texto"]) if len(s.split()) >= 8]
    E = emb.encode(["query: " + s for s, _ in frases], normalize_embeddings=True)
    orden = np.argsort(-(E @ q))[:20]                                  # las 20 frases más pertinentes
    S = nli.predict([(frases[j][0], H) for j in orden], apply_softmax=True, batch_size=16)
    imp = sorted(S[:, 1], reverse=True)[:3]; con = sorted(S[:, 0], reverse=True)[:3]
    si, no = float(np.mean(imp)), float(np.mean(con))
    v = "SÍ" if si > no + 0.15 else ("NO" if no > si + 0.15 else "mixto")
    ok = "✓" if v == esperado[autor] else "✗"
    print(f"\n{ok} {autor:10} {v:6} (esperado {esperado[autor]})   fuerza SÍ {si:.2f} · NO {no:.2f}")
    for lab, col in (("SÍ", 1), ("NO", 0)):
        j = orden[int(S[:, col].argmax())]
        print(f"   {lab} {S[:, col].max():.2f} «{frases[j][0][:200]}» — {frases[j][1][:40]}")
