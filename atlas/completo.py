"""Corpus COMPLETO para búsqueda: todos los pasajes de las 102 obras (sin el tope de 350 por autor de pasajes.py).
Mismo corte que pasajes.py, así los vectores de la muestra se reutilizan tal cual. Salida: completo.json."""
import os, json
from canon import CANON
from pasajes_corte import cuerpo, trozos, SRC
filas = []
for autor, ids in CANON.items():
    for i in ids:
        raw = open(os.path.join(SRC, f'{i}.txt'), encoding='utf-8', errors='ignore').read()
        titulo = next((l[6:].strip() for l in raw[:3000].splitlines() if l.startswith('Title:')), str(i))
        ts = trozos(cuerpo(raw)); n = len(ts); ts = ts[int(n*0.03): n - int(n*0.02)]
        filas += [{'autor': autor, 'obra': titulo, 'gutenberg': i, 'pos': j, 'texto': t} for j, t in enumerate(ts)]
json.dump(filas, open('completo.json', 'w'), ensure_ascii=False)
print('completo.json', len(filas), 'pasajes')
