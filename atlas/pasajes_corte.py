"""Corte de los libros de Gutenberg en pasajes (compartido por pasajes.py y completo.py)."""
import os, re
SRC = os.path.join(os.path.dirname(__file__), '..', 'fuentes', 'gutenberg', 'txt')

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

