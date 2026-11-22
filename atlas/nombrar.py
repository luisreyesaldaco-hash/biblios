"""Nombres legibles para las galaxias y estrellas del colapso (en vez de listas de palabras c-TF-IDF), con
Toponymy (TutteInstitute/toponymy) y un LLM LOCAL en Ollama ($0). NO reagrupa: usa las capas de
colapso_universo_centrado.json tal cual.
Corre en Newton:  nohup .venv-topo/bin/python nombrar.py [modelo] > nombrar.log 2>&1 &   -> nombres.json"""
import json, sys, time, numpy as np
from sentence_transformers import SentenceTransformer
from toponymy import Toponymy, ClusterLayerText
from toponymy.clustering import Clusterer, build_cluster_tree, centroids_from_labels
from toponymy.llm_wrappers import OllamaNamer

MODELO = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:32b"
F = json.load(open("pasajes.json")); V = np.load("vectores.npy").astype(np.float32)
Vc = np.load("vectores_centrados.npy")          # de evoc_comparar.py (mismo centrado que --centrar)
C = json.load(open("colapso_universo_centrado.json"))

def contiguas(l):                                # Toponymy espera etiquetas 0..k-1 (y -1 = polvo)
    l = np.array(l); u = sorted(set(l[l >= 0])); m = {c: i for i, c in enumerate(u)}
    return np.array([m.get(x, -1) for x in l]), u

capas, originales = zip(*(contiguas(C[n]["etiquetas"]) for n in ("estrellas", "galaxias")))   # de fina a gruesa

class Fijo(Clusterer):
    """Devuelve las capas ya calculadas por colapso_universo.py en lugar de agrupar de nuevo."""
    def fit(self, clusterable_vectors, embedding_vectors, layer_class=ClusterLayerText, verbose=None, show_progress_bar=None, **kw):
        self.cluster_tree_ = build_cluster_tree(list(capas))
        self.cluster_layers_ = [layer_class(l, centroids_from_labels(l, embedding_vectors), layer_id=i, **kw) for i, l in enumerate(capas)]
        return self
    def fit_predict(self, *a, **kw):
        self.fit(*a, **kw); return self.cluster_layers_, self.cluster_tree_

class E5:                                        # e5 pide prefijo; las frases clave se comparan con pasajes
    def __init__(self): self.m = SentenceTransformer("intfloat/multilingual-e5-large", device="mps")
    def encode(self, textos, **kw):
        kw.pop("show_progress_bar", None)
        return self.m.encode(["passage: " + t for t in textos], normalize_embeddings=True, batch_size=32, **kw)

t = time.time()
modelo = Toponymy(
    llm_wrapper=OllamaNamer(model=MODELO, llm_specific_instructions=(
        "Write every topic name in Spanish (es-MX), as a philosopher would title a chapter: concrete, 2-6 words. "
        "Name the philosophical theme, never the author or the book."), temperature_override=0.2,
        provider_kwargs={"timeout": 600}),
    text_embedding_model=E5(), clusterer=Fijo(),
    object_description="passages (~200 words) from works of philosophy",
    corpus_description="public-domain English translations of 52 philosophers, from the Presocratics to Russell",
    verbose=True)
modelo.fit([f["texto"] for f in F], V, Vc)
print(f"listo en {(time.time() - t) / 60:.1f} min", flush=True)

res = {"modelo": MODELO}
for nivel, capa, orig in zip(("estrellas", "galaxias"), modelo.cluster_layers_, originales):
    res[nivel] = {str(o): capa.topic_names[i] for i, o in enumerate(orig)}
    viejos = C[nivel]["grupos"]
    for i, o in enumerate(orig):
        print(f"{nivel[:4]} {o:3d}  {capa.topic_names[i]:45s} ← {', '.join(viejos[str(o)]['palabras'][:6])}")
json.dump(res, open("nombres.json", "w"), ensure_ascii=False, indent=1)
