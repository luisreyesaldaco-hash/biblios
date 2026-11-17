"""Embeddings del corpus COMPLETO (corre en Newton). Reutiliza los vectores de la muestra (pasajes.json + vectores.npy)
por texto idéntico. Salida: completo_vectores.npy (float16, normalizados)."""
import json, time, numpy as np, torch
from sentence_transformers import SentenceTransformer
F = json.load(open('completo.json')); t0 = time.time()
M = json.load(open('pasajes.json')); MV = np.load('vectores.npy')
cache = {f['texto']: MV[i] for i, f in enumerate(M)}
falta = [i for i, f in enumerate(F) if f['texto'] not in cache]
print(f'reutilizados {len(F)-len(falta)}, nuevos {len(falta)}', flush=True)
m = SentenceTransformer('intfloat/multilingual-e5-large', device='mps' if torch.backends.mps.is_available() else 'cpu')
m.max_seq_length = 384
V = np.zeros((len(F), 1024), np.float32)
for i, f in enumerate(F):
    if f['texto'] in cache: V[i] = cache[f['texto']]
B = 2048   # por tandas, con avance legible en el log
for k in range(0, len(falta), B):
    idx = falta[k:k+B]
    V[idx] = m.encode(['passage: ' + F[i]['texto'] for i in idx], batch_size=32, normalize_embeddings=True)
    print(f'{min(k+B, len(falta))}/{len(falta)}  {time.time()-t0:.0f}s', flush=True)
np.save('completo_vectores.npy', V.astype(np.float16))
print(f'listo {V.shape} en {time.time()-t0:.0f}s', flush=True)
