"""Diálogos narrados de Platón (Jowett): un párrafo = un turno.
Reglas resuelven 'I said' (narrador) y 'said Glaucon'; lo ambiguo ('he said', sin atribución) lo decide Jev."""
import re, json, pathlib, collections
TXT = pathlib.Path(__file__).resolve().parents[1] / "fuentes/gutenberg/txt"
ROT = re.compile(r"^\s*([A-Z][A-Z']+(?: [A-Z][A-Z']+)?): (.*)", re.S)

# inicio del cuerpo, narrador, ¿'I said' = narrador?, personajes (incluye al narrador y voces anidadas)
NARRADOS = {
 1497: ("I went down yesterday to the Piraeus", "Socrates", True, ["Socrates", "Glaucon", "Adeimantus", "Polemarchus", "Cephalus", "Thrasymachus", "Cleitophon"]),
 1579: ("I was going from the Academy", "Socrates", True, ["Socrates", "Menexenus", "Hippothales", "Lysis", "Ctesippus"]),
 1580: ("Yesterday evening I returned", "Socrates", True, ["Socrates", "Charmides", "Chaerephon", "Critias"]),
 1591: ("COMPANION: Where do you come from", "Socrates", True, ["Socrates", "Companion", "Hippocrates", "Alcibiades", "Critias", "Protagoras", "Hippias", "Prodicus", "Callias"]),
 1598: ("CRITO: Who was the person", "Socrates", True, ["Socrates", "Crito", "Cleinias", "Euthydemus", "Dionysodorus", "Ctesippus"]),
 1600: ("Concerning the things about which", "Apollodorus", False, ["Apollodorus", "Companion", "Aristodemus", "Phaedrus", "Pausanias", "Eryximachus", "Aristophanes", "Agathon", "Socrates", "Diotima", "Alcibiades"]),
 1658: ("ECHECRATES: Were you yourself", "Phaedo", False, ["Phaedo", "Echecrates", "Socrates", "Apollodorus", "Simmias", "Cebes", "Crito", "Xanthippe", "Attendant"]),
 1687: ("We had come from our home at Clazomenae", "Cephalus", False, ["Cephalus", "Adeimantus", "Glaucon", "Antiphon", "Pythodorus", "Socrates", "Zeno", "Parmenides", "Aristoteles"]),
}
VERB = r"(?:said|replied|answered|asked|rejoined|added|continued|cried|exclaimed|interposed|resumed|proceeded|returned|began|retorted)"
YO = re.compile(rf"\b(?:I {VERB}|{VERB} I)\b")
EL = re.compile(rf"\b(?:(?:he|she) {VERB}|{VERB} (?:he|she))\b")

def cuerpo(gid, inicio):
    t = (TXT / f"{gid}.txt").read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n")
    t = t[:t.find("*** END")]
    p = t.rfind("PERSONS OF THE DIALOGUE"); p = t.find(inicio, max(p, 0))
    return t[p:]

def parrafos(gid):
    inicio, narr, yo_es_narr, pers = NARRADOS[gid]
    out = []
    for par in re.split(r"\n\s*\n", cuerpo(gid, inicio)):
        par = " ".join(par.split())
        if not par or re.fullmatch(r"(BOOK [IVXL]+\.?|THE END\.?)", par): continue
        m = ROT.match(par)
        if m:                                   # marco con rótulo (Fedón, Protágoras, Eutidemo)
            out.append({"orador": m.group(1).title(), "texto": m.group(2), "via": "rótulo"}); continue
        cab = " ".join(par.split()[:30]); cands = []
        if yo_es_narr and (y := YO.search(cab)): cands.append((y.start(), narr))
        for n in pers:
            for pat in (rf"\b{VERB} (?:the )?{n}\b", rf"\b{n} {VERB}\b"):
                if (x := re.search(pat, cab)): cands.append((x.start(), n))
        if (e := EL.search(cab)): cands.append((e.start(), None))
        orador = min(cands)[1] if cands else None
        out.append({"orador": orador, "texto": par, "via": "regla" if orador else "?"})
    return out

if __name__ == "__main__":
    for gid in NARRADOS:
        P = parrafos(gid); c = collections.Counter(p["via"] for p in P)
        print(f"{gid}: {len(P):5} párrafos | rótulo {c['rótulo']:4} regla {c['regla']:5} ambiguos {c['?']:5} ({c['?']/len(P):.0%})")
