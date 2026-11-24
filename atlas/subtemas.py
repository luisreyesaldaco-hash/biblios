"""Tercer nivel: cada estrella (tema) se parte en subtemas, lo bastante concretos para tener UNA tesis discutible.
Agrupa con k-medias sobre los vectores centrados por autor (sin la voz de cada uno); k de 2 a 5 por silueta, sin grupos de
menos de 12 pasajes. Las estrellas de menos de 40 pasajes quedan como un solo subtema.
Por cada subtema arma el material para el nombre y la tesis: palabras (c-TF-IDF contra sus hermanos) y pasajes centrales.
Corre en DEMIAN (liviano):  ~/lab/bench-emb-venv/bin/python subtemas.py 11   (la galaxia del piloto)  -> subtemas_g11.json"""
import json, sys, re, collections, numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import CountVectorizer

GAL = int(sys.argv[1])
F = json.load(open('pasajes.json')); V = np.load('vectores.npy')
R = json.load(open('colapso_universo_centrado.json')); G, E = R['galaxias']['etiquetas'], R['estrellas']['etiquetas']
autores = [f['autor'] for f in F]
Vc = V.copy()
for a in set(autores):
    m = np.array([x == a for x in autores]); Vc[m] -= V[m].mean(0)
Vc /= np.linalg.norm(Vc, axis=1, keepdims=True)
Vn = V / np.linalg.norm(V, axis=1, keepdims=True)

# estrellas de la galaxia: la galaxia mayoritaria de sus pasajes
gal_de = {s: collections.Counter(g for g, e in zip(G, E) if e == s).most_common(1)[0][0] for s in set(E) if s >= 0}
estrellas = sorted((s for s, g in gal_de.items() if g == GAL), key=lambda s: -E.count(s))

def palabras(textos, otros, k=8):
    cv = CountVectorizer(stop_words='english', token_pattern=r'(?u)\b[a-zA-Z]{4,}\b', min_df=2)
    X = cv.fit_transform([' '.join(textos), ' '.join(otros) or 'x']).toarray().astype(float)
    tf = X / X.sum(1, keepdims=True); idf = np.log(1 + X.sum() / (X.sum(0) + 1))
    w = cv.get_feature_names_out(); return [w[j] for j in np.argsort(-(tf[0] * idf))[:k]]

def centrales(ix, k=6):   # cercanos al centro (vectores originales), uno por autor
    c = Vn[ix].mean(0); out, vistos = [], set()
    for i in sorted(ix, key=lambda i: -Vn[i] @ c):
        if autores[i] in vistos: continue
        vistos.add(autores[i]); out.append(int(i))
        if len(out) == k: break
    return out

out = []
for s in estrellas:
    ix = np.array([i for i, e in enumerate(E) if e == s])
    mejor = (None, -1, 1)
    if len(ix) >= 40:
        for k in range(2, 6):
            l = KMeans(k, n_init=10, random_state=42).fit_predict(Vc[ix])
            if np.bincount(l).min() < 12: continue
            sc = silhouette_score(Vc[ix], l, metric='cosine')
            if sc > mejor[1]: mejor = (l, sc, k)
    l = mejor[0] if mejor[0] is not None else np.zeros(len(ix), int)
    print(f'estrella {s}: {len(ix)} pasajes -> {mejor[2]} subtemas (silueta {max(mejor[1], 0):.3f})')
    for j in range(l.max() + 1):
        sub = ix[l == j]; her = ix[l != j]
        txt = lambda I: [F[i]['texto'] for i in I]
        out.append({'id': f's{s}_{j}', 'estrella': int(s), 'n': len(sub), 'pasajes': [int(i) for i in sub],
                    'autores': collections.Counter(autores[i] for i in sub).most_common(),
                    'palabras': palabras(txt(sub), txt(her) if len(her) else txt([i for i in range(len(F)) if E[i] != s][:2000])),
                    'centrales': [{'i': i, 'autor': autores[i], 'texto': ' '.join(F[i]['texto'].split()[:130])} for i in centrales(sub)]})
json.dump(out, open(f'subtemas_g{GAL}.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'subtemas ->', f'subtemas_g{GAL}.json')
