"""Postura por orador dentro de una estrella: cada intervención (≥15 palabras) contra una proposición, con Jev.
Uso: postura_estrella.py <estrella> "<proposición>" """
import json, re, sys, pathlib, collections
from concurrent.futures import ThreadPoolExecutor
from jev_oradores import jev, TOK
AQUI = pathlib.Path(__file__).resolve().parent
R = json.load(open(AQUI / "colapso.json")); U = json.load(open(AQUI / "platon_unidades.json"))
est, H = int(sys.argv[1]), sys.argv[2]
ETQ = {"apoya": "The speaker asserts or supports the proposition.",
       "contradice": "The speaker asserts the opposite of the proposition or rejects it.",
       "trata_sin_resolver": "The speaker discusses the topic but does not take a side.",
       "no_trata": "The speaker talks about something else."}
segs = []
for i in [i for i, e in enumerate(R["estrellas"]["etiquetas"]) if e == est]:
    L = [m.groups() for l in U[i]["texto"].split("\n") if (m := re.match(r"([A-Za-z][A-Za-z' ]{0,30}): (.*)", l))]
    for k, (o, t) in enumerate(L):
        if o != "narración" and len(t.split()) >= 15:
            segs.append((U[i]["dialogo"], o, t, [{"speaker": a, "words": b[:600]} for a, b in L[max(0, k - 2):k]]))
q = {"postura": {"type": "choice", "criteria": ETQ, "instructions": "Considering the context, what is the stance of the speaker's words toward the proposition? If the speaker is only restating someone else's view for argument's sake, answer by what the speaker himself holds."}}
def uno(s):
    return jev({"proposition": H, "speaker": s[1], "context_before": s[3], "speaker_words": s[2]}, q["postura"])
with ThreadPoolExecutor(12) as ex: res = list(ex.map(uno, segs))
tab = collections.defaultdict(collections.Counter); mejor = {}
for (d, o, t, _), r in zip(segs, res):
    tab[o][r["choice"]] += 1
    for k in ("apoya", "contradice"):
        p = r["probabilities"][k]
        if p > mejor.get((o, k), (0,))[0]: mejor[(o, k)] = (p, d, t)
print(f"Estrella {est}: {len(segs)} intervenciones | «{H}»\n")
for o, c in sorted(tab.items(), key=lambda kv: -sum(kv[1].values())):
    print(f"{o:13} apoya {c['apoya']:3}  contradice {c['contradice']:3}  sin resolver {c['trata_sin_resolver']:3}  no trata {c['no_trata']:3}")
for o in [o for o, c in sorted(tab.items(), key=lambda kv: -sum(kv[1].values()))][:4]:
    for k in ("apoya", "contradice"):
        if (o, k) in mejor and mejor[(o, k)][0] > 0.8:
            p, d, t = mejor[(o, k)]; print(f"\n[{o} · {k} {p:.2f} · {d}] «{t[:230]}…»")
print(f"\ntokens {TOK[0]:,} ≈${TOK[0]*0.042/1e6:.4f}")
json.dump({"estrella": est, "proposicion": H,
           "tabla": {o: dict(c) for o, c in tab.items()},
           "intervenciones": [{"dialogo": d, "orador": o, "texto": t, "postura": r["choice"], "conf": round(r["confidence"], 3)}
                              for (d, o, t, _), r in zip(segs, res)]},
          open(AQUI / f"posturas_{est}.json", "w"), ensure_ascii=False)
