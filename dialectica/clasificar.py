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
NUCLEO = Q.get("nucleo") or "the specific claim of the proposition itself: its particular case, conditions or exceptions"
ALC = {"especifica": f"The text addresses this specific question: {NUCLEO}.",
       "general": "The text speaks only about the general subject (for example a virtue or a vice in general) and does not consider that specific question."}
def alcance(c):
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone",
        data=json.dumps({"model": "jev-latest", "state": {"proposition": H, "text": c["texto"]},
                         "questions": {"alcance": {"type": "choice", "criteria": ALC,
                            "instructions": f"Does the text consider this specific question: {NUCLEO}? Or does it only speak about the general subject?"}}}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r: d = json.load(r)
    tok[0] += d["usage"]["input_tokens"]; return d["answers"]["alcance"]
toman = [c for c in C if c["postura"] in ("apoya", "contradice")]
with ThreadPoolExecutor(8) as ex:
    for c, r in zip(toman, ex.map(alcance, toman)): c["alcance"], c["alcance_conf"] = r["choice"], round(r["confidence"], 3)
por = collections.defaultdict(list)
for c in C: por[c["autor"]].append(c)
autores = {}
def veredicto(a):   # a ciegas: sin el nombre del autor, solo sus pasajes que tocan el tema
    esp = [c for c in por[a] if c.get("alcance") == "especifica"]
    gen = [c for c in por[a] if c.get("alcance") == "general"]
    ps, nivel = (esp, "expreso") if esp else (gen, "inferido")
    if not ps: return a, {"veredicto": "no_trata", "nivel": "-", "pasajes": len(por[a])}
    r = jev({"proposition": H, "passages": [c["texto"] for c in ps]},
            "Taking all these passages by one author together, what is the author's stance toward the proposition?")
    return a, {"veredicto": r["choice"], "nivel": nivel, "conf": round(r["confidence"], 3), "pasajes": len(por[a]), "relevantes": len(ps),
               "cuenta": dict(collections.Counter(c["postura"] for c in por[a]))}
with ThreadPoolExecutor(8) as ex: autores = dict(ex.map(veredicto, por))
json.dump({"q": Q, "pasajes": C, "autores": autores}, open(AQUI / (Q["id"] + "_dialectica.json"), "w"), ensure_ascii=False, indent=1)
clave = {k: v.split()[0] for k, v in Q.get("clave_previa", {}).items() if not k.startswith("_")}
ca = {a: n for n, l in Q.get("clave_alcance", {}).items() if not n.startswith("_") for a in l}
print(f"Proposición: {H}\n")
orden = {"expreso": 0, "inferido": 1, "-": 2}
for a, v in sorted(autores.items(), key=lambda x: (orden[x[1]["nivel"]], x[1]["veredicto"], -x[1]["pasajes"])):
    if v["nivel"] == "-": continue
    k = clave.get(a, ""); n = ca.get(a, "")
    marca = (f"postura {k} {'✓' if k == v['veredicto'] else '✗'}  " if k else "") + (f"alcance {n} {'✓' if n == v['nivel'] else '✗'}" if n else "")
    print(f"{v['nivel']:9} {a:16} {v['veredicto']:19} {v.get('conf','')!s:6} {marca}")
print("no trata:", ", ".join(a for a, v in autores.items() if v["nivel"] == "-"))
print(f"\ntokens {tok[0]}  costo≈${tok[0]*0.042/1e6:.4f}")
