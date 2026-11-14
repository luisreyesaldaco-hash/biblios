"""Embeddings locales (multilingual-e5-large) + mapa 2D (PCA50 -> t-SNE) + Excel."""
import json, time, numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from openpyxl import Workbook

F = json.load(open('pasajes.json'))
t0 = time.time()
m = SentenceTransformer('intfloat/multilingual-e5-large', device=('mps' if __import__('torch').backends.mps.is_available() else 'cpu'))
m.max_seq_length = 384
import os
cache = {}
if os.path.exists('cache_pasajes.json'):
    cv = np.load('cache_vectores.npy')
    cache = {f['texto']: cv[i] for i, f in enumerate(json.load(open('cache_pasajes.json')))}
falta = [i for i, f in enumerate(F) if f['texto'] not in cache]
print(f'reutilizados {len(F)-len(falta)}, nuevos {len(falta)}', flush=True)
nuevos = m.encode(['passage: ' + F[i]['texto'] for i in falta], batch_size=32, normalize_embeddings=True,
                  show_progress_bar=True).astype(np.float32) if falta else np.zeros((0, 1024), np.float32)
V = np.zeros((len(F), 1024), np.float32)
for i, f in enumerate(F):
    if f['texto'] in cache: V[i] = cache[f['texto']]
for j, i in enumerate(falta): V[i] = nuevos[j]
np.save('vectores.npy', V)
print(f'embeddings {V.shape} en {time.time()-t0:.0f}s', flush=True)

X = PCA(50, random_state=7).fit_transform(V)
XY = TSNE(2, perplexity=40, init='pca', random_state=7, n_jobs=8).fit_transform(X)
np.save('mapa2d.npy', XY)
np.save('mapa3d.npy', TSNE(3, perplexity=40, init='pca', random_state=7, n_jobs=8).fit_transform(X))

autores = list(dict.fromkeys(f['autor'] for f in F))
C = np.stack([V[[i for i, f in enumerate(F) if f['autor'] == a]].mean(0) for a in autores])
C /= np.linalg.norm(C, axis=1, keepdims=True)
D = 1 - C @ C.T

wb = Workbook(); ws = wb.active; ws.title = 'pasajes'
ws.append(['id', 'autor', 'obra', 'gutenberg', 'pos', 'x', 'y', 'texto'])
for i, f in enumerate(F):
    ws.append([i, f['autor'], f['obra'], f['gutenberg'], f['pos'], round(float(XY[i,0]),3), round(float(XY[i,1]),3), f['texto']])
ws2 = wb.create_sheet('autores'); ws2.append(['autor', 'pasajes', 'x_centro', 'y_centro', 'dispersión', 'vecino_más_cercano', 'dist'])
for k, a in enumerate(autores):
    idx = [i for i, f in enumerate(F) if f['autor'] == a]
    disp = float(1 - (V[idx] @ C[k]).mean())
    d = D[k].copy(); d[k] = 9; j = int(d.argmin())
    ws2.append([a, len(idx), round(float(XY[idx,0].mean()),2), round(float(XY[idx,1].mean()),2), round(disp,4), autores[j], round(float(d[j]),4)])
ws3 = wb.create_sheet('distancias'); ws3.append([''] + autores)
for k, a in enumerate(autores): ws3.append([a] + [round(float(x),4) for x in D[k]])
wb.save('universo.xlsx')
print(f'listo en {time.time()-t0:.0f}s', flush=True)
