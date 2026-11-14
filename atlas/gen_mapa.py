"""Genera universo.html: cada filósofo como nebulosa (densidad de sus pasajes en el mapa t-SNE)."""
import json, numpy as np

F = json.load(open('pasajes.json'))
XY = np.load('mapa2d.npy')
V = np.load('vectores.npy')

autores = list(dict.fromkeys(f['autor'] for f in F))  # orden del canon = cronológico
obras = list(dict.fromkeys(f['obra'] for f in F))
C = np.stack([V[[i for i, f in enumerate(F) if f['autor'] == a]].mean(0) for a in autores])
C /= np.linalg.norm(C, axis=1, keepdims=True)
D = 1 - C @ C.T

lo, hi = XY.min(0), XY.max(0)
P = (XY - lo) / (hi - lo)
pts = [[round(float(P[i, 0]), 4), round(float(P[i, 1]), 4), autores.index(f['autor']),
        obras.index(f['obra']), f['texto'][:220]] for i, f in enumerate(F)]
vecinos = {}
for k, a in enumerate(autores):
    orden = [j for j in np.argsort(D[k]) if j != k]
    vecinos[k] = {'cerca': [[int(j), round(float(D[k, j]), 4)] for j in orden[:5]],
                  'lejos': [[int(j), round(float(D[k, j]), 4)] for j in orden[-3:][::-1]]}
datos = {'autores': autores, 'obras': obras, 'pts': pts, 'vecinos': vecinos}

tpl = open('universo_tpl.html', encoding='utf-8').read()
open('universo.html', 'w', encoding='utf-8').write(
    tpl.replace('/*DATOS*/null', json.dumps(datos, ensure_ascii=False, separators=(',', ':'))))
print('universo.html', len(pts), 'puntos')
