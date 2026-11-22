"""¿Se calca un mapa sobre otro? Embeddings e5 (multilingüe) del original y de cada traducción, chunk por chunk.
  1. directo: coseno original↔traducción (incluye el desplazamiento de idioma).
  2. calco: la mejor ROTACIÓN (Procrustes ortogonal, como Mikolov 2013 / Conneau 2018) del espacio original al traducido,
     ajustada SIN el chunk que se evalúa (leave-one-out). Residuo = 1 − coseno(original rotado, traducción).
     Y si el calco ENCUENTRA a su pareja: rango de la traducción correcta entre todas.
  3. dirección: hacia qué otro chunk (por su nombre) se inclina el residuo.
Corre en Newton:  ~/biblios-atlas/.venv-topo/bin/python analizar.py  -> datos/analisis.json"""
import json, collections, numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
D = Path(__file__).parent / "datos"
M = SentenceTransformer("intfloat/multilingual-e5-large", device="mps")
T = collections.defaultdict(dict)
for l in open(D / "traducciones.jsonl"):
    r = json.loads(l); T[(r["corpus"], r["n"])][r["tarea"]] = r["texto"]

def emb(textos, pref="passage: "):
    """Textos largos: ventanas de ~180 palabras (e5 corta en 512 tokens), promedio ponderado por palabras."""
    piezas, dueño, peso = [], [], []
    for i, t in enumerate(textos):
        w = t.split()
        for k in range(0, max(1, len(w)), 180):
            s = w[k:k + 180]; piezas.append(pref + " ".join(s)); dueño.append(i); peso.append(len(s))
    V = M.encode(piezas, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
    out = np.zeros((len(textos), V.shape[1]), np.float32)
    for v, i, p in zip(V, dueño, peso): out[i] += p * v
    return out / np.linalg.norm(out, axis=1, keepdims=True)

def procrustes(S, Tt):
    U, _, Vt = np.linalg.svd(S.T @ Tt); return U @ Vt

def medir(S, Tt, nombres):
    n = len(S); directo = (S * Tt).sum(1)
    pred = np.zeros_like(S)
    for i in range(n):                                    # leave-one-out: la rotación no ve el chunk i
        m = np.arange(n) != i; R = procrustes(S[m], Tt[m]); pred[i] = S[i] @ R
    pred /= np.linalg.norm(pred, axis=1, keepdims=True)
    calco = (pred * Tt).sum(1)
    sims = pred @ Tt.T; rango = (sims > sims[np.arange(n), np.arange(n)][:, None]).sum(1)   # 0 = encontró a su pareja
    off = Tt - S; off_res = np.linalg.norm(off - off.mean(0), axis=1)                     # alternativa simple: restar el desplazamiento medio
    # dirección: el residuo (lo que la rotación no explica) contra los nombres de los OTROS chunks
    res = Tt - pred; Nc = nombres - nombres.mean(0)
    inc = (res / np.linalg.norm(res, axis=1, keepdims=True)) @ (Nc / np.linalg.norm(Nc, axis=1, keepdims=True)).T
    np.fill_diagonal(inc, -9); hacia = inc.argmax(1)
    return {"directo": directo, "calco": calco, "residuo": 1 - calco, "rango": rango, "off_res": off_res, "hacia": hacia, "hacia_cos": inc.max(1)}

R = {}
for corpus, origen, destinos in (("attention", "en", ("es_tonto", "es_bueno")), ("hegel", "de", ("en_dyde", "en_tonto", "en_bueno"))):
    base = json.load(open(D / ("attention_chunks.json" if corpus == "attention" else "hegel_pares.json")))
    base = [b for b in base if all(k in T[(corpus, b["n"])] for k in destinos if k != "en_dyde") and "nombre" in T[(corpus, b["n"])]]
    for b in base: b["en_dyde"] = b.get("en_dyde")
    S = emb([b[origen] for b in base]); nombres = emb([T[(corpus, b["n"])]["nombre"] for b in base], "query: ")
    R[corpus] = {"n": [b["n"] for b in base], "nombres": [T[(corpus, b["n"])]["nombre"] for b in base], "traductores": {}}
    vecs = {}
    for d in destinos:
        Tt = emb([b["en_dyde"] if d == "en_dyde" else T[(corpus, b["n"])][d] for b in base]); vecs[d] = Tt
        m = medir(S, Tt, nombres)
        R[corpus]["traductores"][d] = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in m.items()}
        print(f"{corpus:9s} {d:9s} n={len(base):3d}  directo {m['directo'].mean():.3f}  calco {m['calco'].mean():.3f}"
              f"  residuo mediana {np.median(m['residuo']):.3f}  encuentra pareja {np.mean(m['rango'] == 0):.0%}", flush=True)
    if corpus == "hegel":   # mismas palabras de llegada (inglés): ¿dónde se separa el humano de las máquinas?
        R[corpus]["dyde_vs_bueno"] = (vecs["en_dyde"] * vecs["en_bueno"]).sum(1).tolist()
        R[corpus]["dyde_vs_tonto"] = (vecs["en_dyde"] * vecs["en_tonto"]).sum(1).tolist()
        R[corpus]["bueno_vs_tonto"] = (vecs["en_bueno"] * vecs["en_tonto"]).sum(1).tolist()
        print(f"hegel inglés↔inglés: Dyde~bueno {np.mean(R[corpus]['dyde_vs_bueno']):.3f}  Dyde~tonto {np.mean(R[corpus]['dyde_vs_tonto']):.3f}"
              f"  bueno~tonto {np.mean(R[corpus]['bueno_vs_tonto']):.3f}", flush=True)
json.dump(R, open(D / "analisis.json", "w"), ensure_ascii=False)
print("FIN analizar")
