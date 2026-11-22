"""Hegel, Filosofía del derecho: el original alemán (DiBiPhil/Zeno, TEI) y la traducción inglesa de Dyde (1896, OCR de Cornell),
empatados POR NÚMERO DE § (no por embeddings: alinear con lo mismo que luego se mide sería circular).
Cada unidad = § + su nota (Anmerkung) de Hegel. Dyde sí trae los Zusätze de Gans ("Addition. —"): se cortan, el alemán no los tiene.
Uso: python3 preparar_hegel.py [§max]  -> datos/hegel_pares.json"""
import re, sys, json, html
from pathlib import Path
D = Path(__file__).parent / "datos"
MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 360

# --- alemán: <p rend="h4">§ N</p> seguido de sus <p> hasta el siguiente encabezado
x = (D / "hegel_rechtsphilosophie.xml").read_text()
x = re.sub(r"<pb[^>]*/>|<lb/>", " ", x)
de, actual = {}, None
for m in re.finditer(r'<p( [^>]*)?>(.*?)</p>', x, re.S):
    attrs, cuerpo = m.group(1) or "", m.group(2)
    texto = html.unescape(re.sub(r"<[^>]+>", "", cuerpo)); texto = re.sub(r"\s+", " ", texto).strip()
    if 'rend="h' in attrs:                       # encabezado: o abre un §, o cierra el anterior (títulos de parte/sección)
        n = re.fullmatch(r"§ ?(\d+)", texto)
        actual = int(n.group(1)) if n else None
        if actual: de[actual] = []
        continue
    if actual and texto: de[actual].append(texto)
de = {k: " ".join(v) for k, v in de.items() if v}

# --- inglés (Dyde): desde la Introducción, líneas "N. Texto" con N creciente; fuera cabezas de página y títulos en mayúsculas
L = (D / "dyde_1896_ocr.txt").read_text().splitlines()
ini = next(i for i, l in enumerate(L) if l.strip() == "INTRODUCTION." and i > 1100)
L = [re.sub(r"^\s*I\. +The philosophic", "1. The philosophic", l) for l in L]   # el OCR leyó el §1 como "I."
en, n_prev, buf = {}, 0, None
def cabeza(l):
    s = l.strip()
    if not s: return False
    if re.match(r"^\d+\s+[A-Z .,'’]+$", s) or re.match(r"^[A-Z .,'’]+\s+\d+$", s): return True   # "30 THE PHILOSOPHY OF RIGHT."
    letras = [c for c in s if c.isalpha()]
    return len(letras) > 6 and sum(c.isupper() for c in letras) / len(letras) > 0.8              # títulos de parte/sección
for l in L[ini:]:
    m = re.match(r"^\s*(\d{1,3})\. +(.*)", l)
    if m and n_prev < int(m.group(1)) <= n_prev + 4:
        n_prev = int(m.group(1)); buf = en.setdefault(n_prev, []); buf.append(m.group(2)); continue
    if buf is not None and not cabeza(l): buf.append(l.strip())
def limpiar(ls):
    t = "\n".join(ls)
    t = re.split(r"\bAddition\.\s*[—-]", t)[0]   # fuera los Zusätze de Gans (el alemán de Zeno no los trae)
    t = re.sub(r"\bNote\.\s*[—-]\s*", "", t)       # la etiqueta de las notas (el alemán no la pone)
    t = re.sub(r"-\s*\n\s*", "", t)              # palabras cortadas al final de línea
    return re.sub(r"\s+", " ", t).strip()
en = {k: limpiar(v) for k, v in en.items()}

pares = [{"n": k, "de": de[k], "en_dyde": en[k], "palabras_de": len(de[k].split()), "palabras_en": len(en[k].split())}
         for k in sorted(set(de) & set(en)) if k <= MAX]
# control de calidad del empate: la razón de longitudes inglés/alemán debe ser estable (~1.2-1.5); fuera los que no
import statistics
r = [p["palabras_en"] / p["palabras_de"] for p in pares]; med = statistics.median(r)
buenos = [p for p, x in zip(pares, r) if 0.6 * med < x < 1.6 * med]
print(f"§ en alemán: {len(de)} · en Dyde (OCR): {len(en)} · en ambos (≤§{MAX}): {len(pares)} · razón en/de mediana {med:.2f}"
      f" · descartados por longitud dispareja: {sorted(p['n'] for p in pares if p not in buenos)}")
json.dump(buenos, open(D / "hegel_pares.json", "w"), ensure_ascii=False, indent=1)
print(f"{len(buenos)} pares · palabras alemán {sum(p['palabras_de'] for p in buenos):,} · inglés {sum(p['palabras_en'] for p in buenos):,}")
