"""Traduce chunk por chunk con dos modelos LOCALES de Ollama (Newton, $0) y nombra cada chunk.
  tonto = llama3.1:8b · bueno = qwen2.5:32b
  Attention: inglés -> español.  Hegel: alemán -> inglés (para comparar contra Dyde, el traductor humano de 1896).
Guarda cada resultado al terminarlo (traducciones.jsonl): si Newton se duerme o se corta, se relanza y sigue donde iba.
Uso (Newton): nohup .venv-topo/bin/python -u traducir.py > traducir.log 2>&1 &"""
import json, re, time, urllib.request
from pathlib import Path
D = Path(__file__).parent / "datos"; SAL = D / "traducciones.jsonl"
MODELOS = {"tonto": "llama3.1:8b", "bueno": "qwen2.5:32b"}
hecho = set()
if SAL.exists():
    for l in SAL.open(): r = json.loads(l); hecho.add((r["corpus"], r["n"], r["tarea"]))

def ollama(modelo, prompt):
    req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps({
        "model": modelo, "prompt": prompt, "stream": False,
        "options": {"temperature": 0, "num_ctx": 8192, "seed": 42}}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r: return json.load(r)["response"].strip()

def trozos(t, max_pal=260):           # los § largos se traducen por pedazos de oraciones (igual para los dos modelos)
    ors = re.split(r"(?<=[.!?;])\s+", t); out, buf = [], []
    for o in ors:
        buf.append(o)
        if len(" ".join(buf).split()) > max_pal: out.append(" ".join(buf)); buf = []
    if buf: out.append(" ".join(buf))
    return out

PROMPT = {"es": "Translate the following English text into Spanish. Output ONLY the Spanish translation, nothing else.\n\n{t}",
          "en": "Translate the following German text into English. Output ONLY the English translation, nothing else.\n\n{t}"}
NOMBRE = ("Give a short Spanish title (3 to 6 words) naming the specific topic of this passage, as a chapter title. "
          "Output ONLY the title, without quotes.\n\n{t}")
def limpiar(r):                      # los modelos chicos a veces anteponen "Here is the translation:"
    return re.sub(r"^(here is|here's|aquí está|aquí tienes)[^:\n]*:\s*", "", r, flags=re.I).strip().strip('"')

tareas = []
A = json.load(open(D / "attention_chunks.json")); H = json.load(open(D / "hegel_pares.json"))
for clave in ("tonto", "bueno"):
    tareas += [("attention", c["n"], f"es_{clave}", c["en"], clave, "es") for c in A]
tareas += [("attention", c["n"], "nombre", c["en"], "bueno", None) for c in A]
for clave in ("tonto", "bueno"):
    tareas += [("hegel", p["n"], f"en_{clave}", p["de"], clave, "en") for p in H]
tareas += [("hegel", p["n"], "nombre", p["de"], "bueno", None) for p in H]
pend = [t for t in tareas if (t[0], t[1], t[2]) not in hecho]
print(f"{len(tareas)} tareas · {len(tareas) - len(pend)} ya hechas · {len(pend)} pendientes", flush=True)
t0 = time.time()
with SAL.open("a") as f:
    for k, (corpus, n, tarea, texto, clave, idioma) in enumerate(pend, 1):
        if idioma: r = " ".join(limpiar(ollama(MODELOS[clave], PROMPT[idioma].format(t=x))) for x in trozos(texto))
        else: r = limpiar(ollama(MODELOS[clave], NOMBRE.format(t=" ".join(texto.split()[:400]))))
        f.write(json.dumps({"corpus": corpus, "n": n, "tarea": tarea, "modelo": MODELOS[clave], "texto": r}, ensure_ascii=False) + "\n"); f.flush()
        if k % 10 == 0 or k == len(pend):
            print(f"{time.strftime('%H:%M')} {k}/{len(pend)} ({corpus} {tarea}) · {(time.time() - t0) / k:.1f} s/tarea", flush=True)
print("FIN traducir", flush=True)
