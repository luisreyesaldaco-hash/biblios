"""Tercer nivel → quaestiones: cada subtema con su tesis (borrador de qwen, revisada con Luis el 24-nov-2026) se vuelve un qNNN
en dialectica/sub/, con sus pasajes como candidatos (todos los del subtema, sin búsqueda). La CLAVE se fija aquí, ANTES de correr Jev.
s33_0 no se corre: es q002 al revés (se reutiliza q002). s38_1 se quitó: casi todo Kierkegaard, sin debate.
Uso: python3 sub_preparar.py  → sub/*.json ; luego  for q in sub/s*[0-9].json; do python3 clasificar.py $q; done"""
import json, pathlib
AQUI = pathlib.Path(__file__).resolve().parent; SUB = AQUI / "sub"; SUB.mkdir(exist_ok=True)
F = json.load(open(AQUI.parent / "atlas/pasajes.json"))
S = {s["id"]: s for s in json.load(open(AQUI.parent / "atlas/subtemas_g11.json"))}
T = {t["id"]: t for t in json.load(open(AQUI.parent / "atlas/tesis_g11.json"))}
# Ajustes a mano a los borradores de qwen (None = se queda el de qwen)
AJ = {
 "s33_1": ("The human will necessarily tends toward the good: no one wills what they believe to be evil.",
           "La voluntad humana tiende necesariamente al bien: nadie quiere lo que cree que es un mal.",
           "whether the will can knowingly will evil, or necessarily wills what it takes to be good"),
 "s55_0": None, "s55_1": None,
 "s56_0": (None, "El principio moral supremo se deriva de la razón humana y no de la autoridad divina.", None),
 "s56_1": None,
 "s23_0": ("Virtue is a kind of knowledge: whoever truly knows the good will do it.",
           "La virtud es conocimiento: quien conoce de verdad el bien, lo hace.",
           "whether knowing the good is sufficient for acting well, or whether virtue also needs habit, will or passion"),
 "s23_1": None,
 "s23_2": ("Virtue can be taught.", "La virtud se puede enseñar.",
           "whether virtue can be acquired by instruction, or only by nature, habit or grace"),
 "s38_0": None, "s38_2": None,
}
# Clave previa (de historia de la filosofía, sin ver a Jev). (?) = caso dudoso.
CLAVE = {
 "s33_1": {"Tomás de Aquino": "apoya", "Leibniz": "apoya", "Plotino": "apoya", "Schopenhauer": "contradice",
           "Kant": "contradice (?) mal radical: la voluntad puede elegir contra la ley", "Feuerbach": "apoya (?)", "Emerson": "apoya (?)"},
 "s55_0": {"Adam Smith": "apoya", "Hume": "apoya", "Kant": "apoya", "Schopenhauer": "apoya", "Tomás de Aquino": "apoya", "Pascal": "apoya",
           "Spinoza": "contradice", "Stirner": "contradice", "Feuerbach": "contradice (?)", "Locke": "contradice (?)", "Mill": "apoya (?)"},
 "s55_1": {"Adam Smith": "contradice", "Hume": "contradice"},
 "s56_0": {"Kant": "apoya", "Mill": "apoya", "Spencer": "apoya", "Dewey": "apoya", "Rousseau": "apoya (?)",
           "Tomás de Aquino": "contradice (?) la ley natural es razón, pero participa de la ley eterna"},
 "s56_1": {"Kant": "apoya", "Tomás de Aquino": "apoya", "Adam Smith": "apoya (?)", "Mill": "contradice", "Spencer": "contradice",
           "Hume": "contradice (?)", "Dewey": "contradice (?)"},
 "s23_0": {"Tomás de Aquino": "contradice", "Pascal": "contradice", "Adam Smith": "contradice", "Hobbes": "contradice (?)", "Mill": "contradice (?)"},
 "s23_1": {"Adam Smith": "contradice", "Séneca": "contradice", "Marco Aurelio": "contradice"},
 "s23_2": {"Schopenhauer": "contradice", "Plotino": "contradice (?)", "Tomás de Aquino": "apoya (?)", "Hegel": "apoya (?)"},
 "s38_0": {"Mill": "apoya", "Marx y Engels": "contradice", "Spencer": "contradice (?) critica el utilitarismo empírico de Bentham"},
 "s38_2": {"Schopenhauer": "apoya", "Rousseau": "apoya", "Nietzsche": "contradice", "Spencer": "trata_sin_resolver (?)"},
}
for sid, aj in AJ.items():
    t, s = T[sid], S[sid]
    en, es, nu = aj if aj else (None, None, None)
    q = {"id": sid, "estrella": s["estrella"], "subtema": t["nombre"],
         "proposicion": en or t["tesis"], "proposicion_es": es or t["tesis_es"], "nucleo": nu or t["nucleo"],
         "origen": "Tercer nivel del mapa (subtema de la galaxia 11); tesis: borrador de qwen2.5:32b revisado a mano.",
         "clave_previa": {"_nota": "Fijada ANTES de correr (24-nov-2026).", **CLAVE[sid]}}
    json.dump(q, open(SUB / f"{sid}.json", "w"), ensure_ascii=False, indent=1)
    C = [{"i": str(i), "autor": F[i]["autor"], "obra": F[i]["obra"], "pos": str(F[i]["pos"]), "texto": F[i]["texto"],
          "estrella": str(s["estrella"]), "subtema": sid} for i in s["pasajes"]]
    json.dump({"id": sid, "corpus": "subtema", "candidatos": C}, open(SUB / f"{sid}_candidatos.json", "w"), ensure_ascii=False, indent=1)
    print(sid, len(C), "pasajes ·", q["proposicion"])
