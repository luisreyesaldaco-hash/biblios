"""Jev vs. el caso que tumbó al NLI: 'ideas innatas' sobre los mismos top-10 pasajes por autor."""
import json, pathlib, urllib.request
from concurrent.futures import ThreadPoolExecutor
AQUI = pathlib.Path(__file__).resolve().parent
KEY = dict(l.split("=", 1) for l in (AQUI.parent / ".env").read_text().splitlines() if "=" in l)["TYPESAFE_API_KEY"].strip()
TOP = json.load(open(AQUI / "top10_innatas.json"))
H = "The mind has innate ideas that do not come from the senses or experience."
CLAVE = {"Platón": "SÍ", "Descartes": "SÍ", "Leibniz": "SÍ", "Locke": "NO", "Hume": "NO", "Berkeley": "NO", "Kant": "matiz"}
ETQ = {"apoya": "The text asserts or supports the proposition.",
       "contradice": "The text asserts the opposite of the proposition or rejects it.",
       "trata_sin_resolver": "The text discusses the topic of the proposition but does not take a side.",
       "no_trata": "The text is about something else."}
Q = {"postura": {"type": "choice", "instructions": "What is the stance of the text toward the proposition?", "criteria": ETQ}}
tok = [0]
def jev(state, questions=Q):
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone",
        data=json.dumps({"model": "jev-latest", "state": state, "questions": questions}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    tok[0] += d["usage"]["input_tokens"]; return d["answers"]["postura"]

res = {}
for autor, ps in TOP.items():
    with ThreadPoolExecutor(5) as ex:
        R = list(ex.map(lambda p: jev({"proposition": H, "text": p["texto"]}), ps))
    ap = [r["probabilities"]["apoya"] for r in R]; co = [r["probabilities"]["contradice"] for r in R]
    v = "SÍ" if max(ap) > 0.6 and max(ap) > max(co) else ("NO" if max(co) > 0.6 else "calla")
    # por autor: los 10 pasajes juntos
    G = jev({"proposition": H, "author": autor, "passages": [p["texto"] for p in ps]},
            {"postura": {"type": "choice", "instructions": "Taking all passages by this author together, what is the author's stance toward the proposition?", "criteria": ETQ}})
    g = {"apoya": "SÍ", "contradice": "NO"}.get(G["choice"], "calla")
    cuenta = {k: sum(r["choice"] == k for r in R) for k in ETQ}
    j = (ap if v != "NO" else co).index(max(ap if v != "NO" else co))
    res[autor] = dict(pasaje=v, autor=g, autor_p={k: round(x, 2) for k, x in G["probabilities"].items()}, cuenta=cuenta,
                      ap=max(ap), co=max(co), cita=ps[j]["texto"][:240], obra=ps[j]["obra"])
    print(f"{autor:10} clave={CLAVE[autor]:5} | por pasaje: {v:5} (apoya máx {max(ap):.2f}, contradice máx {max(co):.2f}) {cuenta}"
          f" | por autor: {g:5} {res[autor]['autor_p']}", flush=True)
for modo in ("pasaje", "autor"):
    ok = sum(res[a][modo] == CLAVE[a] for a in CLAVE if CLAVE[a] != "matiz")
    print(f"aciertos {modo}: {ok}/6 (sin Kant)")
json.dump(res, open(AQUI / "jev_innatas_res.json", "w"), ensure_ascii=False, indent=1)
print(f"tokens de entrada: {tok[0]}  costo≈${tok[0]*0.042/1e6:.4f}")
