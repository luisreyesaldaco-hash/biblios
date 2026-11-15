"""Prueba mínima de Jev (TypeSafe): ¿distingue afirmar de negar? Control que los embeddings fallaron."""
import json, pathlib, urllib.request

ENV = pathlib.Path(__file__).resolve().parents[1] / ".env"
KEY = dict(l.split("=", 1) for l in ENV.read_text().splitlines() if "=" in l)["TYPESAFE_API_KEY"].strip()

TESIS = "All knowledge comes from experience."
TEXTOS = {
    "afirma": "There are no innate ideas: every idea in the mind was first received through the senses and reflection on them.",
    "niega": "Some knowledge owes nothing to experience; the mind possesses certain truths prior to and independent of any sensation.",
    "otro_tema": "The sovereign must keep the peace and collect taxes so that commerce between the provinces can flourish.",
    "sin_resolver": "Whether all our knowledge derives from experience is a question philosophers have long disputed, and it deserves careful examination.",
}
ETIQUETAS = {
    "apoya": "The text asserts or supports the proposition.",
    "contradice": "The text asserts the opposite of the proposition or rejects it.",
    "trata_sin_resolver": "The text discusses the topic of the proposition but does not take a side.",
    "no_trata": "The text is about something else.",
}

def jev(state, questions):
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone",
        data=json.dumps({"model": "jev-latest", "state": state, "questions": questions}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:500]}

tok = 0
for nombre, texto in TEXTOS.items():
    r = jev({"proposition": TESIS, "text": texto}, {
        "postura": {"type": "choice", "instructions": "What is the stance of the text toward the proposition?", "criteria": ETIQUETAS},
        "afirma": {"type": "noul", "instructions": "Does the text affirm the proposition?"},
    })
    if "error" in r:
        print(nombre, r); break
    a = r["answers"]; tok += r["usage"]["input_tokens"]
    p = {k: round(v, 2) for k, v in a["postura"]["probabilities"].items()}
    print(f"{nombre:13s} → {a['postura']['choice']:19s} conf={a['postura']['confidence']:.2f}  sí/no={a['afirma']['noul']:.2f}  {p}")
print("modelo:", r.get("model"), " tokens de entrada:", tok, f" costo≈${tok*0.042/1e6:.6f}")
