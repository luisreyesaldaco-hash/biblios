"""Atlas filosófico, ensayo 1: gnoseología (¿de dónde viene el conocimiento?).
Distancia coseno entre tesis con multilingual-e5-large (local, sin API).
Las tesis son paráfrasis breves, no citas: miden cercanía de lo que dicen las paráfrasis."""
import numpy as np
from sentence_transformers import SentenceTransformer

TESIS = {
 'Platón':      'Conocer es recordar: el alma ya contempló las Ideas eternas y los sentidos solo nos hacen recordarlas.',
 'Aristóteles': 'Nada hay en el entendimiento que no haya pasado antes por los sentidos; el intelecto abstrae la forma universal de las cosas sensibles.',
 'Descartes':   'La razón posee ideas innatas claras y distintas; los sentidos engañan y solo el pensamiento que duda de todo halla una certeza: pienso, luego existo.',
 'Leibniz':     'Las verdades necesarias de la razón no vienen de la experiencia; el entendimiento las contiene en germen, como las vetas en el mármol.',
 'Locke':       'La mente nace como una hoja en blanco; todas nuestras ideas proceden de la experiencia, por sensación o por reflexión.',
 'Berkeley':    'Ser es ser percibido; no hay materia fuera de la mente, solo ideas percibidas por espíritus.',
 'Hume':        'Todas nuestras ideas son copias de impresiones; la causalidad no se conoce por razón sino por hábito y costumbre.',
 'Kant':        'Todo conocimiento comienza con la experiencia, pero no todo procede de ella: el sujeto impone formas a priori que hacen posible la experiencia.',
 'Hegel':       'La verdad es el todo; el saber se desarrolla dialécticamente hasta que el espíritu se conoce a sí mismo como saber absoluto.',
 'Pirrón':      'Ninguna afirmación puede justificarse mejor que su contraria; hay que suspender el juicio y así se alcanza la serenidad.',
 'Nietzsche':   'No hay hechos, solo interpretaciones; todo conocimiento es una perspectiva al servicio de la vida.',
 'Peirce':      'El significado de una idea son sus consecuencias prácticas; la verdad es aquello en lo que convergería la investigación.',
 'Popper':      'Ninguna teoría se verifica por inducción; la ciencia avanza conjeturando y refutando, y una teoría vale si puede ser falsada.',
}
CONTROL = {
 'C+': 'El conocimiento proviene de la experiencia.',
 'C-': 'El conocimiento no proviene de la experiencia.',
 'C0': 'La receta del mole poblano lleva chocolate y chiles.',
}

m = SentenceTransformer('intfloat/multilingual-e5-large', device='cpu')
def emb(d):
    v = m.encode(['query: ' + t for t in d.values()], normalize_embeddings=True)
    return list(d), v

n, V = emb(TESIS)
cn, CV = emb(CONTROL)
S = V @ V.T
D = 1 - S

print('== Control (¿el embedding ve la negación?) ==')
print(f"  C+ vs C- (contrarias):   dist {1-CV[0]@CV[1]:.3f}")
print(f"  C+ vs C0 (otro tema):    dist {1-CV[0]@CV[2]:.3f}")

print('\n== Matriz de distancias (1 - coseno) ==')
w = 6
print(' ' * 12 + ''.join(x[:w].rjust(w + 1) for x in n))
for i, a in enumerate(n):
    print(a[:12].ljust(12) + ''.join(f'{D[i,j]:.3f}'.rjust(w + 1) for j in range(len(n))))

pares = sorted((D[i, j], n[i], n[j]) for i in range(len(n)) for j in range(i + 1, len(n)))
print('\n== 5 más cercanos ==')
for d, a, b in pares[:5]: print(f'  {d:.3f}  {a} — {b}')
print('== 5 más lejanos ==')
for d, a, b in pares[-5:][::-1]: print(f'  {d:.3f}  {a} — {b}')

# Eje tesis/antítesis al estilo Atlas: racionalismo (Descartes+Leibniz) ↔ empirismo (Locke+Hume)
polo_r = V[[n.index('Descartes'), n.index('Leibniz')]].mean(0)
polo_e = V[[n.index('Locke'), n.index('Hume')]].mean(0)
eje = polo_r - polo_e; eje /= np.linalg.norm(eje)
medio = (polo_r + polo_e) / 2
proy = {a: float((V[i] - medio) @ eje) for i, a in enumerate(n)}
mx = max(abs(x) for x in proy.values())
print('\n== Eje  EMPIRISMO (Locke+Hume) ◄──► RACIONALISMO (Descartes+Leibniz) ==')
for a, x in sorted(proy.items(), key=lambda kv: kv[1]):
    pos = int((x / mx + 1) * 20)
    print(f'  {a:12} {"·"*pos}●{"·"*(40-pos)}  {x:+.3f}')
