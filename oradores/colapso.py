"""La nebulosa que colapsa (Platón): e5 → UMAP 10D → HDBSCAN en dos escalas (galaxias y estrellas).
Corre en Newton Max. Entrada: platon_unidades.json. Salida: colapso.json + platon_vectores.npy."""
import json, re, os, collections, numpy as np, torch, umap
from sklearn.cluster import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
U = json.load(open("platon_unidades.json"))
limpio = [re.sub(r"(?m)^[A-Za-z][A-Za-z' ]{0,30}: ", "", u["texto"]) for u in U]   # sin nombres de orador
if os.path.exists("platon_vectores.npy") and len(np.load("platon_vectores.npy")) == len(U):
    V = np.load("platon_vectores.npy")
else:
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("intfloat/multilingual-e5-large", device="mps" if torch.backends.mps.is_available() else "cpu")
    V = m.encode(["passage: " + t for t in limpio], batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    np.save("platon_vectores.npy", V)
X10 = umap.UMAP(n_components=10, n_neighbors=15, min_dist=0.0, metric="cosine", random_state=42).fit_transform(V)
X2 = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, metric="cosine", random_state=42).fit_transform(V)

# palabras que distinguen a cada grupo (c-TF-IDF); fuera nombres propios de personajes y muletillas de Jowett
nombres = {w.lower() for u in U for w in u["voces"]} | {"socrates", "said", "say", "says", "replied", "yes", "true", "certainly",
           "shall", "did", "does", "thing", "things", "think", "know", "like", "just", "let", "tell", "speak", "mean", "way", "ought"}
cv = CountVectorizer(stop_words="english", min_df=3, token_pattern=r"(?u)\b[a-zA-Z]{3,}\b")
C = cv.fit_transform(limpio); vocab = np.array(cv.get_feature_names_out())
ok = np.array([w not in nombres for w in vocab])

def grupos(lbl):
    out = {}
    for c in sorted(set(lbl) - {-1}):
        idx = np.where(lbl == c)[0]
        tf = np.asarray(C[idx].sum(0)).ravel() / max(1, C[idx].sum())
        idf = np.log(1 + len(U) / (1 + np.asarray((C > 0).sum(0)).ravel()))
        s = tf * idf * ok
        cen = V[idx].mean(0); rep = idx[np.argsort(-(V[idx] @ cen))[:3]]
        voces = collections.Counter()
        for i in idx:
            for o, n in U[i]["voces"].items(): voces[o] += n
        out[int(c)] = {"n": len(idx), "palabras": vocab[np.argsort(-s)[:10]].tolist(),
                       "voces": voces.most_common(5), "dialogos": collections.Counter(U[i]["dialogo"] for i in idx).most_common(4),
                       "rep": [int(i) for i in rep]}
    return out

res = {}
for nivel, mcs in (("galaxias", 60), ("estrellas", 12)):
    lbl = HDBSCAN(min_cluster_size=mcs, min_samples=5).fit_predict(X10)
    res[nivel] = {"etiquetas": lbl.tolist(), "grupos": grupos(lbl), "ruido": int((lbl == -1).sum())}
    print(f"{nivel}: {len(res[nivel]['grupos'])} grupos, ruido {res[nivel]['ruido']} de {len(U)}")
res["xy"] = X2.round(4).tolist()
json.dump(res, open("colapso.json", "w"), ensure_ascii=False)
