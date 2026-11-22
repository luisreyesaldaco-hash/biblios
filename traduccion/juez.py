"""Juez independiente: Jev compara cada original con su traducción y dice si se conservó el sentido.
Sirve para probar si el residuo de los embeddings PREDICE los errores reales (si sí: detectar errores sin leer, gratis).
Corre en DEMIAN (llave de Jev en ../.env):  python3 juez.py  -> datos/juez.json"""
import json, collections, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
AQUI = Path(__file__).resolve().parent; D = AQUI / "datos"
KEY = dict(l.split("=", 1) for l in (AQUI.parent / ".env").read_text().splitlines() if "=" in l)["TYPESAFE_API_KEY"].strip()
CRIT = {"fiel": "The translation conveys the full meaning of the source; differences are only of wording or style.",
        "desviacion_menor": "The translation is mostly faithful but softens, shifts or loses some nuance, term or emphasis of the source.",
        "error_de_sentido": "The translation changes, omits or adds meaning: some claim of the source is not what the translation says."}
T = collections.defaultdict(dict)
for l in open(D / "traducciones.jsonl"):
    r = json.loads(l); T[(r["corpus"], r["n"])][r["tarea"]] = r["texto"]
casos = []
for c in json.load(open(D / "attention_chunks.json")):
    casos += [("attention", c["n"], d, c["en"], T[("attention", c["n"])][d]) for d in ("es_tonto", "es_bueno") if d in T[("attention", c["n"])]]
for p in json.load(open(D / "hegel_pares.json")):
    casos += [("hegel", p["n"], "en_dyde", p["de"], p["en_dyde"])]
    casos += [("hegel", p["n"], d, p["de"], T[("hegel", p["n"])][d]) for d in ("en_tonto", "en_bueno") if d in T[("hegel", p["n"])]]
tok = [0]
def jev(c):
    _, _, _, src, tr = c
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=json.dumps({
        "model": "jev-latest", "state": {"source": src, "translation": tr},
        "questions": {"fidelidad": {"type": "choice", "criteria": CRIT,
                                    "instructions": "Compare the translation with the source text. Is the meaning preserved?"}}}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r: d = json.load(r)
    tok[0] += d["usage"]["input_tokens"]; a = d["answers"]["fidelidad"]; return a["choice"], round(a["confidence"], 3)
with ThreadPoolExecutor(8) as ex: R = list(ex.map(jev, casos))
out = [{"corpus": c[0], "n": c[1], "traductor": c[2], "juicio": r[0], "conf": r[1]} for c, r in zip(casos, R)]
json.dump(out, open(D / "juez.json", "w"), ensure_ascii=False, indent=1)
for k, g in sorted(collections.Counter((o["corpus"], o["traductor"], o["juicio"]) for o in out).items()): print(k, g)
print(f"tokens {tok[0]}  costo≈${tok[0] * 0.042 / 1e6:.4f}")
