"""Fase 3 de la dialéctica (corre en DEMIAN, donde está la llave de Jev): postura de cada pasaje y veredicto por autor a ciegas.
Uso: python clasificar.py q001.json  → q001_dialectica.json"""
import json, sys, pathlib, collections, urllib.request
from concurrent.futures import ThreadPoolExecutor
AQUI = pathlib.Path(__file__).resolve().parent
KEY = dict(l.split("=", 1) for l in (AQUI.parent / ".env").read_text().splitlines() if "=" in l)["TYPESAFE_API_KEY"].strip()
Q = json.load(open(sys.argv[1])); C = json.load(open(AQUI / (Q["id"] + "_candidatos.json")))["candidatos"]
H = Q["proposicion"]
ETQ = {"apoya": "The text asserts or supports the proposition.",
       "contradice": "The text asserts the opposite of the proposition or rejects it.",
       "trata_sin_resolver": "The text discusses the topic of the proposition but does not take a side.",
       "no_trata": "The text is about something else."}
tok = [0]
def jev(state, instr):
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone",
        data=json.dumps({"model": "jev-latest", "state": state,
                         "questions": {"postura": {"type": "choice", "instructions": instr, "criteria": ETQ}}}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r: d = json.load(r)
    tok[0] += d["usage"]["input_tokens"]; return d["answers"]["postura"]
with ThreadPoolExecutor(8) as ex:
    R = list(ex.map(lambda c: jev({"proposition": H, "text": c["texto"]}, "What is the stance of the text toward the proposition?"), C))
for c, r in zip(C, R): c["postura"], c["conf"] = r["choice"], round(r["confidence"], 3)
por = collections.defaultdict(list)
for c in C: por[c["autor"]].append(c)
autores = {}
def veredicto(a):   # a ciegas: sin el nombre del autor, solo sus pasajes que tocan el tema
    ps = [c for c in por[a] if c["postura"] != "no_trata"]
    if not ps: return a, {"veredicto": "no_trata", "pasajes": len(por[a])}
    r = jev({"proposition": H, "passages": [c["texto"] for c in ps]},
            "Taking all these passages by one author together, what is the author's stance toward the proposition?")
    return a, {"veredicto": r["choice"], "conf": round(r["confidence"], 3), "pasajes": len(por[a]), "relevantes": len(ps),
               "cuenta": dict(collections.Counter(c["postura"] for c in por[a]))}
with ThreadPoolExecutor(8) as ex: autores = dict(ex.map(veredicto, por))
json.dump({"q": Q, "pasajes": C, "autores": autores}, open(AQUI / (Q["id"] + "_dialectica.json"), "w"), ensure_ascii=False, indent=1)
clave = {k: v.split()[0] for k, v in Q.get("clave_previa", {}).items() if not k.startswith("_")}
print(f"Proposición: {H}\n")
for a, v in sorted(autores.items(), key=lambda x: (x[1]["veredicto"], -x[1]["pasajes"])):
    k = clave.get(a, ""); ok = "" if not k else ("✓" if k == v["veredicto"] else "✗")
    print(f"{a:16} {v['veredicto']:19} {v.get('conf','')!s:6} {v.get('cuenta','')}  {('clave: ' + k + ' ' + ok) if k else ''}")
print(f"\ntokens {tok[0]}  costo≈${tok[0]*0.042/1e6:.4f}")
