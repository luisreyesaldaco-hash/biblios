"""Resuelve el orador de los párrafos ambiguos de los diálogos narrados con Jev, y compara con la alternancia."""
import json, pathlib, time, urllib.request, urllib.error, collections, sys
from concurrent.futures import ThreadPoolExecutor
from narrados import NARRADOS, parrafos
AQUI = pathlib.Path(__file__).resolve().parent
KEY = dict(l.split("=", 1) for l in (AQUI.parent / ".env").read_text().splitlines() if "=" in l)["TYPESAFE_API_KEY"].strip()
TIT = {1497: "Republic", 1579: "Lysis", 1580: "Charmides", 1591: "Protagoras", 1598: "Euthydemus", 1600: "Symposium", 1658: "Phaedo", 1687: "Parmenides"}
TOK = [0]

def jev(state, q):
    body = json.dumps({"model": "jev-latest", "state": state, "questions": {"x": q}}).encode()
    for intento in range(6):
        try:
            req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=body,
                  headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.load(r); TOK[0] += d["usage"]["input_tokens"]; return d["answers"]["x"]
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            if getattr(e, "code", 500) in (400, 401, 403, 422): raise
            time.sleep(2 ** intento)
    raise RuntimeError("Jev no respondió")

def alternancia(P):
    """Línea base sin modelo: un párrafo sin firma lo dice el otro de los dos últimos oradores."""
    ult, out = [], []
    for p in P:
        s = p["orador"]
        if s is None:
            s = ult[-2] if len(ult) >= 2 else (ult[-1] if ult else None)
        out.append(s)
        if s and (not ult or ult[-1] != s): ult = (ult + [s])[-2:]
    return out

def tramo(gid, P, a, b):
    inicio, narr, yo, pers = NARRADOS[gid]
    crit = {n: f"These words are spoken by {n}." for n in pers}
    crit["narration"] = f"Narrative description by {narr} of scene or action, not anyone's reported words."
    q = {"type": "choice", "criteria": crit, "instructions":
         "Who speaks the words in 'paragraph'? Unattributed short replies usually alternate between the two people in conversation."}
    for i in range(a, b):
        if P[i]["orador"] is not None: continue
        prev = [{"speaker": P[j].get("orador") or "?", "text": P[j]["texto"][:350]} for j in range(max(0, i - 6), i)]
        st = {"dialogue": f"Plato, {TIT[gid]} (Jowett)", "narrator": narr + (" — narrates as 'I'" if yo else ""),
              "characters": pers, "previous": prev, "paragraph": P[i]["texto"][:1500]}
        r = jev(st, q)
        P[i].update(orador=r["choice"], via="jev", conf=round(r["confidence"], 3))

if __name__ == "__main__":
    gids = [int(x) for x in sys.argv[1:]] or list(NARRADOS)
    todo = {}
    for gid in gids:
        P = parrafos(gid); base = alternancia(P)
        for p, s in zip(P, base): p["alterna"] = s
        todo[gid] = P
    trabajos = [(g, a, min(a + 250, len(P))) for g, P in todo.items() for a in range(0, len(P), 250)]
    t0 = time.time()
    with ThreadPoolExecutor(16) as ex:
        list(ex.map(lambda w: tramo(w[0], todo[w[0]], w[1], w[2]), trabajos))
    for gid, P in todo.items():
        J = [p for p in P if p["via"] == "jev"]
        acuerdo = sum(p["orador"] == p["alterna"] for p in J)
        dudosos = sum(p["conf"] < 0.7 for p in J)
        pal = collections.Counter()
        for p in P: pal[p["orador"]] += len(p["texto"].split())
        print(f"{TIT[gid]:11} jev={len(J):5} acuerdo con alternancia {acuerdo/len(J):.0%}  conf<0.7: {dudosos:4} | "
              + ", ".join(f"{o} {n}" for o, n in pal.most_common(6)), flush=True)
        json.dump(P, open(AQUI / f"{gid}_turnos.json", "w"), ensure_ascii=False)
    print(f"{time.time()-t0:.0f} s, tokens {TOK[0]:,}, ≈${TOK[0]*0.042/1e6:.3f}")

# Correcciones con dato del texto: tramos donde solo conversan ciertos personajes.
TRAMOS_CERRADOS = {1687: [(141, ["Parmenides", "Aristoteles"])]}  # 'Ask, and I will answer' (párr. 140)

def cerrar(gid):
    P = json.load(open(AQUI / f"{gid}_turnos.json"))
    inicio, narr, yo, pers = NARRADOS[gid]
    for desde, solo in TRAMOS_CERRADOS[gid]:
        q = {"type": "choice", "criteria": {n: f"These words are spoken by {n}." for n in solo},
             "instructions": "Who speaks the words in 'paragraph'? Only these two people are talking: one asks, the other answers."}
        idx = [i for i in range(desde, len(P)) if P[i]["via"] == "jev"]
        def uno(i):
            prev = [{"speaker": P[j]["orador"] if P[j]["via"] != "jev" else "?", "text": P[j]["texto"][:350]} for j in range(max(0, i - 6), i)]
            r = jev({"dialogue": f"Plato, {TIT[gid]} (Jowett)", "characters": solo, "previous": prev, "paragraph": P[i]["texto"][:1500]}, q)
            P[i].update(orador=r["choice"], conf=round(r["confidence"], 3), via="jev-cerrado")
        with ThreadPoolExecutor(16) as ex: list(ex.map(uno, idx))
    json.dump(P, open(AQUI / f"{gid}_turnos.json", "w"), ensure_ascii=False)
    return P
