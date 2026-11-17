"""Página de una quaestio: tesis y antítesis por autor, con sus citas.
Uso: python gen_pagina.py q001  → q001.html (desde q001_dialectica.json y pagina_tpl.html)"""
import json, sys, pathlib, re
AQUI = pathlib.Path(__file__).resolve().parent
qid = sys.argv[1] if len(sys.argv) > 1 else "q001"
D = json.load(open(AQUI / f"{qid}_dialectica.json"))
Q, A = D["q"], D["autores"]
DUDOSO = 0.4

def citas(a, v):
    """Los pasajes que sostienen el veredicto: los del nivel que se usó (expreso o inferido), más los que no toman partido."""
    nivel = {"expreso": "especifica", "inferido": "general"}.get(v["nivel"])
    ps = [p for p in D["pasajes"] if p["autor"] == a and (p.get("alcance") == nivel or p["postura"] == "trata_sin_resolver")]
    ps.sort(key=lambda p: (p["postura"] != v["veredicto"], p["postura"] == "trata_sin_resolver", -p["conf"]))
    out = []
    for p in ps:
        voz = None
        if a == "Platón" and re.search(r"\bPlato(nic)?\b", p["texto"]):
            voz = "Parece de la introducción del traductor (Jowett), no de Platón."
        out.append({"obra": p["obra"], "pos": p["pos"], "postura": p["postura"], "conf": p["conf"],
                    "alcance": p.get("alcance"), "texto": p["texto"], "voz": voz})
    return out

autores = []
for a, v in A.items():
    r = {"autor": a, "veredicto": v["veredicto"], "nivel": v["nivel"], "conf": v.get("conf"),
         "pasajes": v["pasajes"], "relevantes": v.get("relevantes", 0), "cuenta": v.get("cuenta", {})}
    r["dudoso"] = r["conf"] is not None and r["conf"] < DUDOSO and r["veredicto"] != "no_trata"
    r["citas"] = citas(a, v) if v["nivel"] != "-" else []
    autores.append(r)

datos = {"id": Q["id"], "proposicion": Q["proposicion"], "proposicion_es": Q.get("proposicion_es"),
         "nucleo": Q.get("nucleo"), "tesis": Q["tesis"], "antitesis": Q["antitesis"],
         "terminos": Q.get("terminos", []), "autores": autores, "total_pasajes": len(D["pasajes"]),
         "dudoso": DUDOSO}
tpl = (AQUI / "pagina_tpl.html").read_text()
html = tpl.replace("/*DATOS*/null", json.dumps(datos, ensure_ascii=False))
(AQUI / f"{qid}.html").write_text(html)
print(f"{qid}.html  {len(html)//1024} KB  autores={len(autores)}")
