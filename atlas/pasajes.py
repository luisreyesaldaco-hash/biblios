"""Parte cada libro en pasajes de ~120-260 palabras, sin cabecera/licencia de Gutenberg.
Tope por autor (muestreo estratificado por obra) para que nadie domine el mapa."""
import os, re, json, random
from canon import CANON
SRC = os.path.join(os.path.dirname(__file__), '..', 'fuentes', 'gutenberg', 'txt')
TOPE = 350
random.seed(7)

def cuerpo(t):
    a = re.search(r'\*\*\* ?START OF.*?\*\*\*', t); b = re.search(r'\*\*\* ?END OF', t)
    return t[a.end() if a else 0: b.start() if b else len(t)]

def trozos(t):
    pars = [re.sub(r'\s+', ' ', p).strip() for p in re.split(r'\n\s*\n', t)]
    buf, out = [], []
    for p in pars:
        if not p: continue
        buf.append(p)
        n = sum(len(x.split()) for x in buf)
        if n >= 120:
            out.append(' '.join(buf)); buf = []
    out = [o if len(o.split()) <= 260 else ' '.join(o.split()[:260]) for o in out]
    # fuera índices, tablas, notas: exige prosa
    return [o for o in out if sum(c.isalpha() for c in o) / len(o) > 0.75 and o.count('.') >= 2]

filas = []
for autor, ids in CANON.items():
    por_obra = {}
    for i in ids:
        raw = open(os.path.join(SRC, f'{i}.txt'), encoding='utf-8', errors='ignore').read()
        titulo = next((l[6:].strip() for l in raw[:3000].splitlines() if l.startswith('Title:')), str(i))
        ts = trozos(cuerpo(raw))
        n = len(ts); ts = ts[int(n*0.03): n - int(n*0.02)]  # recorta prólogos/índices de bordes
        por_obra[(i, titulo)] = ts
    total = sum(len(v) for v in por_obra.values())
    # Cuota pareja por obra (water-filling): lo que no usa una obra corta pasa a las largas.
    cuota, resto, pend = {}, TOPE, dict(por_obra)
    while pend and resto > 0:
        parte = resto // len(pend) or 1
        cortas = {k: v for k, v in pend.items() if len(v) <= parte}
        if not cortas:
            for k in pend: cuota[k] = parte
            break
        for k, v in cortas.items(): cuota[k] = len(v); resto -= len(v); del pend[k]
    for (i, titulo), ts in por_obra.items():
        k = min(len(ts), cuota.get((i, titulo), 0))
        for j in sorted(random.sample(range(len(ts)), k)):
            filas.append({'autor': autor, 'obra': titulo, 'gutenberg': i, 'pos': j, 'texto': ts[j]})
    print(f'{autor:16} {sum(1 for f in filas if f["autor"]==autor):4} de {total:5} | ' + ' · '.join(f'{t[:18]} {sum(1 for f in filas if f["obra"]==t and f["autor"]==autor)}' for (_, t) in por_obra))
json.dump(filas, open('pasajes.json', 'w'), ensure_ascii=False)
print('total', len(filas))
