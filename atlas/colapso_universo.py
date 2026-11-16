"""La nebulosa que colapsa, para los 52 filósofos (--centrar: sin el acento de cada autor + asignación del ruido por vecinos): vectores e5 (ya hechos) → UMAP 10D → HDBSCAN en dos escalas.
Corre en Newton Max. Entrada: pasajes.json + vectores.npy. Salida: colapso_universo.json."""
import json, sys, collections, numpy as np, umap
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
F = json.load(open("pasajes.json")); V = np.load("vectores.npy"); assert len(F) == len(V)
args = [x for x in sys.argv[1:] if not x.startswith("--")]
MG, ME = (int(x) for x in (args[:2] if len(args) > 1 else (120, 25)))
CENTRAR = "--centrar" in sys.argv   # quitar el "acento" de cada autor: restar su vector promedio antes de agrupar
SALIDA = "colapso_universo_centrado.json" if CENTRAR else "colapso_universo.json"
if CENTRAR:
    aut = np.array([f["autor"] for f in F]); V = V.copy(); media = V.mean(0)
    for a in set(aut): V[aut == a] += media - V[aut == a].mean(0)
    V /= np.linalg.norm(V, axis=1, keepdims=True)
X10 = umap.UMAP(n_components=10, n_neighbors=30 if CENTRAR else 15, min_dist=0.0, metric="cosine", random_state=42).fit_transform(V)
textos = [f["texto"] for f in F]
fuera = {"gutenberg", "project", "ebook", "chapter", "book", "thou", "thee", "thy", "hath", "doth", "shall", "said", "say",
         "thing", "things", "think", "know", "like", "just", "let", "mean", "way", "ought", "does", "did", "make", "made", "yes", "unto", "tis", "chap", "footnote", "sidenote", "note", "obj", "reply", "prop", "hyl", "phil", "hor", "cleo", "iii", "vol", "page", "ibid"}
cv = CountVectorizer(stop_words="english", min_df=5, token_pattern=r"(?u)\b[a-zA-Z]{3,}\b")
C = cv.fit_transform(textos); vocab = np.array(cv.get_feature_names_out())
ok = np.array([w not in fuera for w in vocab])
idf = np.log(1 + len(F) / (1 + np.asarray((C > 0).sum(0)).ravel()))

def grupos(lbl):
    out = {}
    for c in sorted(set(lbl) - {-1}):
        idx = np.where(lbl == c)[0]
        s = np.asarray(C[idx].sum(0)).ravel() / max(1, C[idx].sum()) * idf * ok
        cen = V[idx].mean(0); rep = idx[np.argsort(-(V[idx] @ cen))[:3]]
        out[int(c)] = {"n": len(idx), "palabras": vocab[np.argsort(-s)[:10]].tolist(),
                       "autores": collections.Counter(F[i]["autor"] for i in idx).most_common(6),
                       "obras": collections.Counter(F[i]["obra"] for i in idx).most_common(4), "rep": [int(i) for i in rep]}
    return out

res = {}
for nivel, mcs in (("galaxias", MG), ("estrellas", ME)):
    lbl = HDBSCAN(min_cluster_size=mcs, min_samples=5).fit_predict(X10)
    if CENTRAR:   # HDBSCAN deja ~2/3 como ruido: cada pasaje suelto se une al tema de 9+ de sus 15 vecinos de núcleo
        nucleo, suelto = np.where(lbl >= 0)[0], np.where(lbl < 0)[0]
        _, ix = NearestNeighbors(n_neighbors=15).fit(X10[nucleo]).kneighbors(X10[suelto])
        lbl0 = lbl.copy()
        for p, vec in zip(suelto, ix):
            c, n = collections.Counter(lbl0[nucleo[vec]]).most_common(1)[0]
            if n >= 9: lbl[p] = c
    res[nivel] = {"etiquetas": lbl.tolist(), "grupos": grupos(lbl), "ruido": int((lbl == -1).sum())}
    print(f"{nivel} (mcs {mcs}): {len(res[nivel]['grupos'])} grupos, ruido {res[nivel]['ruido']} de {len(F)}", flush=True)
json.dump(res, open(SALIDA, "w"), ensure_ascii=False)
