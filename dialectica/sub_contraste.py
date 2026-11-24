"""Segunda opinión con el mismo lector: la TESIS NEGADA. Jev vuelve a leer cada pasaje contra la negación de la tesis.
Si lee bien, apoya <-> contradice se invierten y 'sin resolver' / 'no trata' se quedan igual. Lo que no se invierte es dudoso.
Uso (DEMIAN):  python3 sub_contraste.py  -> sub/<id>_contraste.json + resumen"""
import json, sys, pathlib, collections, urllib.request
from concurrent.futures import ThreadPoolExecutor
AQUI = pathlib.Path(__file__).resolve().parent; SUB = AQUI / "sub"
KEY = dict(l.split("=", 1) for l in (AQUI.parent / ".env").read_text().splitlines() if "=" in l)["TYPESAFE_API_KEY"].strip()
NEG = {  # negaciones escritas a mano (24-nov-2026)
 "s33_1": "The human will does not necessarily tend toward the good: a person can knowingly will what they believe to be evil.",
 "s55_0": "Self-love can be the sole motive of virtuous actions.",
 "s55_1": "Moral approbation is not derived from self-love but from an inherent moral sense or sentiment.",
 "s56_0": "The ultimate moral principle is not derived from human rationality alone but depends on divine authority.",
 "s56_1": "Moral goodness is primarily determined by the consequences of actions rather than by their inherent nature.",
 "s23_0": "Virtue is not a kind of knowledge: one can truly know the good and still fail to do it.",
 "s23_1": "The highest good in life is not the pursuit of pleasure.",
 "s23_2": "Virtue cannot be taught.",
 "s38_0": "The principle of utility is not the sole criterion for moral action.",
 "s38_2": "Altruistic behavior is motivated by calculated self-interest rather than by a natural desire to alleviate suffering.",
}
ETQ = {"apoya": "The text asserts or supports the proposition.",
       "contradice": "The text asserts the opposite of the proposition or rejects it.",
       "trata_sin_resolver": "The text discusses the topic of the proposition but does not take a side.",
       "no_trata": "The text is about something else."}
ESPERA = {"apoya": "contradice", "contradice": "apoya", "trata_sin_resolver": "trata_sin_resolver", "no_trata": "no_trata"}
tok = [0]
def jev(H, texto):
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=json.dumps({"model": "jev-latest",
        "state": {"proposition": H, "text": texto},
        "questions": {"postura": {"type": "choice", "instructions": "What is the stance of the text toward the proposition?", "criteria": ETQ}}}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r: d = json.load(r)
    tok[0] += d["usage"]["input_tokens"]; return d["answers"]["postura"]
total = collections.Counter()
for sid, H in NEG.items():
    D = json.load(open(SUB / f"{sid}_dialectica.json")); P = D["pasajes"]
    with ThreadPoolExecutor(8) as ex: R = list(ex.map(lambda c: jev(H, c["texto"]), P))
    out = []
    for c, r in zip(P, R):
        ok = ESPERA[c["postura"]] == r["choice"]
        toma = c["postura"] in ("apoya", "contradice")
        out.append({"i": c["i"], "autor": c["autor"], "postura": c["postura"], "negada": r["choice"], "conf_neg": round(r["confidence"], 3), "coherente": ok})
        total["n"] += 1; total["ok"] += ok; total["toma"] += toma; total["toma_ok"] += toma and ok
    json.dump({"id": sid, "negacion": H, "pasajes": out}, open(SUB / f"{sid}_contraste.json", "w"), ensure_ascii=False, indent=1)
    tm = [o for o in out if o["postura"] in ("apoya", "contradice")]
    print(f"{sid}: {sum(o['coherente'] for o in out)}/{len(out)} coherentes · de los que toman postura: {sum(o['coherente'] for o in tm)}/{len(tm)}"
          + "  dudosos: " + ", ".join(f"{a} {n}" for a, n in collections.Counter(o['autor'] for o in tm if not o['coherente']).most_common(4)), flush=True)
print(f"\nTOTAL {total['ok']}/{total['n']} coherentes ({total['ok']/total['n']:.0%}) · toman postura: {total['toma_ok']}/{total['toma']} ({total['toma_ok']/max(1,total['toma']):.0%})")
print(f"tokens {tok[0]}  costo≈${tok[0]*0.042/1e6:.4f}")
