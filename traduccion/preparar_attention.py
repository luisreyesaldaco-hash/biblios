"""Control: "Attention Is All You Need" (Vaswani et al., 2017, arXiv 1706.03762). Texto técnico: su traducción debería
desviarse poco. Párrafos de prosa por sección (sin referencias, tablas, ecuaciones sueltas ni pies de figura).
El PDF tiene derechos: vive en datos/ (fuera de git), nunca en fuentes/.
Uso: python3 preparar_attention.py  -> datos/attention_chunks.json"""
import re, json, fitz
from pathlib import Path
D = Path(__file__).parent / "datos"
doc = fitz.open(D / "attention.pdf")
chunks, seccion = [], "Abstract"
for pg in doc:
    for b in pg.get_text("blocks"):
        t = re.sub(r"-\n(?=[a-z])", "", b[4]); t = re.sub(r"\s+", " ", t).strip()
        if re.fullmatch(r"(\d+(\.\d+)*)\s+[A-Z][A-Za-z\- ,]{2,60}", t):        # encabezado de sección: "3.2.1 Scaled Dot-Product Attention"
            seccion = t; continue
        if t.startswith("References"): break
        pal = t.split()
        letras = sum(c.isalpha() for c in t) / max(1, len(t))
        if len(pal) < 35 or letras < 0.72 or t.startswith(("Figure", "Table", "∗")) or "Equal contribution" in t: continue
        chunks.append({"seccion": seccion, "en": t})
    else: continue
    break
# trozos de ~60-220 palabras: los párrafos largos se parten por oraciones
out = []
for c in chunks:
    ors = re.split(r"(?<=[.!?])\s+(?=[A-Z])", c["en"]); buf = []
    for o in ors:
        buf.append(o)
        if len(" ".join(buf).split()) > 160: out.append({"seccion": c["seccion"], "en": " ".join(buf)}); buf = []
    if buf:
        if out and out[-1]["seccion"] == c["seccion"] and len(" ".join(buf).split()) < 40: out[-1]["en"] += " " + " ".join(buf)
        else: out.append({"seccion": c["seccion"], "en": " ".join(buf)})
for i, c in enumerate(out): c["n"] = i
json.dump(out, open(D / "attention_chunks.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "chunks ·", sum(len(c["en"].split()) for c in out), "palabras ·", len({c["seccion"] for c in out}), "secciones")
for c in out[:4] + out[-2:]: print(f"  [{c['seccion'][:28]}] {c['en'][:110]}")
