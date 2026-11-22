"""Genera universo.html: cada filósofo como nebulosa (densidad de sus pasajes en el mapa t-SNE)."""
import json, numpy as np

F = json.load(open('pasajes.json'))
XY = np.load('mapa3d.npy')
V = np.load('vectores.npy')

autores = list(dict.fromkeys(f['autor'] for f in F))  # orden del canon = cronológico
obras = list(dict.fromkeys(f['obra'] for f in F))
C = np.stack([V[[i for i, f in enumerate(F) if f['autor'] == a]].mean(0) for a in autores])
C /= np.linalg.norm(C, axis=1, keepdims=True)
D = 1 - C @ C.T

lo, hi = XY.min(0), XY.max(0)
P = (XY - XY.mean(0)) / np.abs(XY - XY.mean(0)).max()
pts = [[round(float(P[i, 0]), 4), round(float(P[i, 1]), 4), round(float(P[i, 2]), 4), autores.index(f['autor']),
        obras.index(f['obra']), f['texto'][:220]] for i, f in enumerate(F)]
vecinos = {}
for k, a in enumerate(autores):
    orden = [j for j in np.argsort(D[k]) if j != k]
    vecinos[k] = {'cerca': [[int(j), round(float(D[k, j]), 4)] for j in orden[:5]],
                  'lejos': [[int(j), round(float(D[k, j]), 4)] for j in orden[-3:][::-1]]}
# Sub-nebulosas: obras de cada autor, distancia entre sus centros (espacio completo).
porObra = {}
for i, f in enumerate(F): porObra.setdefault((autores.index(f['autor']), obras.index(f['obra'])), []).append(i)
obrasAutor, distObras = {}, {}
for k in range(len(autores)):
    ks = [o for (a, o) in porObra if a == k]
    obrasAutor[k] = [[o, len(porObra[(k, o)])] for o in ks]
    cs = np.stack([V[porObra[(k, o)]].mean(0) for o in ks]); cs /= np.linalg.norm(cs, axis=1, keepdims=True)
    distObras[k] = [[round(float(x), 4) for x in fila] for fila in (1 - cs @ cs.T)]
# Colapso por temas (colapso_universo.json, de Newton): galaxias y estrellas; cada pasaje conserva el color de su autor.
from gravedad import colapsar
R = json.load(open('colapso_universo_centrado.json'))   # sin el acento de cada autor (ver colapso_universo.py --centrar)
G, E = R['galaxias']['etiquetas'], R['estrellas']['etiquetas']
Q, gal_de, gal_de_pt = colapsar(P, G, E, hueco_gal=0.3, abrir=1.5, cielo=1.35)
for i, p in enumerate(pts):
    p += [gal_de_pt[i], E[i], round(float(Q[i, 0]), 4), round(float(Q[i, 1]), 4), round(float(Q[i, 2]), 4)]
# Nombres legibles: Toponymy + qwen2.5:32b local (nombrar.py, en Newton) -> nombres.json, con 6 correcciones a mano (20-nov-2026).
NOMBRES = json.load(open('nombres.json'))
NOMBRES['galaxias'].update({'1': 'Kant y la Crítica de la Ética',    # no es Kant: Schopenhauer, Peirce, James hablando de él
                            '6': 'Estado, Ley y Gobierno',           # 'Poder Legislativo' le quedaba chico
                            '7': 'Clase Obrera y Explotación',       # errata
                            '5': 'Relatos, Anécdotas e Historia'})   # no es Platón (8%): es el género narrativo, anécdota y diálogo
NOMBRES['estrellas'].update({'55': 'Simpatía y Aprobación Moral',    # repetía el nombre de la galaxia 11 (Smith, Hume)
                             '26': 'Consuelo y Pérdida Familiar', '58': 'Cantidad y Relatividad'})   # erratas
# Pasajes centrales de cada estrella: los más cercanos a su centro en los vectores ORIGINALES (en el espacio centrado salían
# pasajes genéricos), uno por autor para que se vea quién y cómo habla del tema.
Vn = V / np.linalg.norm(V, axis=1, keepdims=True)
def centrales(s, k=3):
    idx = np.where(np.array(E) == s)[0]; cen = Vn[idx].mean(0)
    out, vistos = [], set()
    for i in idx[np.argsort(-(Vn[idx] @ cen))]:
        if F[i]['autor'] in vistos: continue
        out.append(int(i)); vistos.add(F[i]['autor'])
        if len(out) == k: break
    return out
temas = {'galaxias': {int(k): {'n': v['n'], 'nombre': NOMBRES['galaxias'][k], 'palabras': v['palabras'][:5], 'autores': v['autores']}
                      for k, v in R['galaxias']['grupos'].items() if int(k) in set(gal_de.values())},
         'estrellas': {int(k): {'n': v['n'], 'nombre': NOMBRES['estrellas'][k], 'palabras': v['palabras'][:5], 'autores': v['autores'], 'galaxia': gal_de[int(k)], 'rep': centrales(int(k))}
                       for k, v in R['estrellas']['grupos'].items()}}
print(len(temas['galaxias']), 'galaxias con estrellas,', len(temas['estrellas']), 'estrellas')
# Quaestiones sacadas del mapa (dialectica/q*_dialectica.json con 'estrella' en cada pasaje): postura de cada pasaje según Jev.
import glob
quaestiones = []
for f in sorted(glob.glob('../dialectica/q*_dialectica.json')):
    D = json.load(open(f)); Cq = D['pasajes']
    if not all('estrella' in c for c in Cq): continue
    clave = {k: v.split()[0] for k, v in D['q'].get('clave_previa', {}).items() if not k.startswith('_')}
    quaestiones.append({'id': D['q']['id'], 'prop': D['q']['proposicion_es'], 'estrellas': sorted({int(c['estrella']) for c in Cq}),
                        'postura': {int(c['i']): c['postura'][0] for c in Cq},   # a(poya) c(ontradice) t(rata sin resolver) n(o trata)
                        'autores': {a: {'v': v['veredicto'], 'nivel': v['nivel'], 'conf': v.get('conf'), 'clave': clave.get(a),
                                        'cuenta': v.get('cuenta', {})} for a, v in D['autores'].items() if v['nivel'] != '-'}})
print(len(quaestiones), 'quaestiones del mapa')
datos = {'autores': autores, 'temas': temas, 'quaestiones': quaestiones, 'obras': obras, 'pts': pts, 'vecinos': vecinos,
         'obrasAutor': obrasAutor, 'distObras': distObras}

tpl = open('universo3d_tpl.html', encoding='utf-8').read()
open('universo3d.html', 'w', encoding='utf-8').write(
    tpl.replace('/*DATOS*/null', json.dumps(datos, ensure_ascii=False, separators=(',', ':'))))
print('universo3d.html', len(pts), 'puntos')
