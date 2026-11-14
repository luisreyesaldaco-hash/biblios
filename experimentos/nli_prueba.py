import json, numpy as np, torch
from sentence_transformers import SentenceTransformer, CrossEncoder
dev = "mps" if torch.backends.mps.is_available() else "cpu"
nli = CrossEncoder("cross-encoder/nli-deberta-v3-large", device=dev)
ETQ = ["contradice", "implica", "neutral"]   # orden de salida del modelo
def juzga(pares):
    s = nli.predict(pares, apply_softmax=True, batch_size=16)
    return s
print("== Control: ¿ve la negación? ==")
H = "Knowledge comes from experience."
for p in ["All our knowledge is derived from experience.", "Knowledge does not come from experience; it is innate.", "Mole poblano is made with chocolate and chiles."]:
    s = juzga([(p, H)])[0]; print(f"  {ETQ[int(s.argmax())]:10} {s.round(2)}  | {p}")

F = json.load(open("pasajes.json")); V = np.load("vectores.npy")
emb = SentenceTransformer("intfloat/multilingual-e5-large", device=dev)
H = "The mind has innate ideas that do not come from the senses or experience."
q = emb.encode(["query: " + H], normalize_embeddings=True)[0]
print("\n== Tesis:", H, "==")
for autor in ["Platón", "Descartes", "Leibniz", "Locke", "Hume", "Berkeley", "Kant"]:
    idx = [i for i, f in enumerate(F) if f["autor"] == autor]
    top = sorted(idx, key=lambda i: -float(V[i] @ q))[:10]          # embeddings: encontrar
    S = juzga([(F[i]["texto"], H) for i in top])                    # NLI: elegir
    imp, con = S[:, 1], S[:, 0]
    veredicto = "SÍ" if imp.max() > 0.6 and imp.max() > con.max() else ("NO" if con.max() > 0.6 else "calla")
    j = top[int(imp.argmax() if veredicto != "NO" else con.argmax())]
    print(f"\n{autor:10} {veredicto:5} implica máx {imp.max():.2f} · contradice máx {con.max():.2f}")
    print("   «" + F[j]["texto"][:260] + "…»  —", F[j]["obra"][:45])
