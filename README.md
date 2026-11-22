# biblios — a map of philosophy

An experiment in mapping 2,500 years of philosophy, cheaply first, carefully after:

1. **The map (cheap).** 16,277 passages from 52 philosophers (public-domain English translations from
   Project Gutenberg, sampled evenly per work) embedded with `intfloat/multilingual-e5-large`, run locally,
   with $0 in API costs. Clustered in two scales (UMAP 10D + HDBSCAN): *galaxies* (broad themes) and
   *stars* (specific topics). Topics are named by a local LLM (Toponymy + `qwen2.5:32b`), and the result
   is rendered as an interactive 3D universe (Three.js).
2. **The theses (careful).** Embeddings tell you *what a passage is about*, not *what it claims*:
   "X" and "not X" land almost on top of each other. So a second layer asks an LLM judge, passage by
   passage and blind to the author, whether each text supports or rejects a proposition, then aggregates
   a verdict per author. The expected answers are written down **before** running.

The working notes and code comments are in Spanish.

## Findings so far

- **Style versus ideas.** Before any correction, 58.7% of a passage's nearest neighbours come from the
  same author (chance: 2.0%), and 92–95% of those come from the *same work*. Neighbourhoods follow the
  voice of the translation more than the idea. Subtracting each author's mean vector drops this to 26.4%
  and the clusters' NMI with author from 0.76 to 0.17 (`atlas/termometro.py`).
- **Off-the-shelf clustering.** EVōC labels 62–79% of passages as noise on this corpus, so the
  two-scale collapse with neighbour reassignment stays (`atlas/evoc_comparar.py`).
- **Stance needs a reader.** *Lying to save a life* (q001) and *Is the will free?* (q002): the judge
  separates supporters from opponents inside a single topic cluster. On q002 it matched 11 of the 14
  pre-registered expectations; at least one of the misses was an error in the expectations themselves
  (Leibniz). Judge cost: a few cents per question.
- **Translation does not show up in the vectors** (`traduccion/`). Hegel's *Philosophy of Right*
  (257 §§, German) was translated by a small (`llama3.1:8b`) and a larger (`qwen2.5:32b`) local model,
  then compared with Dyde's 1896 human translation. *Attention Is All You Need* (EN→ES) served as a
  technical control. Method: an orthogonal Procrustes map between the two embedding spaces, evaluated
  leave-one-out, scored on residuals and on whether each source passage retrieves its own translation.
  - Topic maps align well: machine translations retrieve their source paragraph 87–89% of the time.
  - The embedding residual does **not** predict translation errors flagged by the LLM judge (AUC ≈ 0.5).
    The two models are nearly identical in vector space (cosine 0.98), but the judge finds 46 meaning
    errors in the small model and 9 in the larger one.
  - The machines collapse Hegel's central distinction *Sittlichkeit* (ethical life) vs *Moralität*
    (morality) by rendering *Sittlichkeit* as "morality", and turn *aufgehoben* into "abolished". Dyde,
    with his 19th-century vocabulary, sits *farthest* from the source in vector space (54%) yet keeps the
    distinction ("ethical": 80 times).
  - In short: close on the map, far in the concept. Concept-level errors are invisible to vector
    similarity.
  - Caveats: Dyde's OCR has typos, there is a single judge, and the cases have not been reviewed by hand yet.

## Layout

| Dir | What |
|---|---|
| `atlas/` | corpus → passages → embeddings → clustering → topic names → 2D/3D pages |
| `dialectica/` | questions (`qNNN.json`), candidate retrieval, blind per-passage stance, per-author verdicts |
| `oradores/` | speaker attribution inside Plato's dialogues |
| `traduccion/` | the translation experiment |
| `experimentos/` | small probes (negation controls, NLI) |
| `MAPA.md` | the longer-term idea: one modal logic, and therefore one formal language, per branch of philosophy |

## Running

```bash
cd atlas
python3 bajar.py && python3 pasajes.py      # download Gutenberg texts, cut passages
python embeber.py                           # embeddings (GPU/MPS recommended)
python colapso_universo.py                  # galaxies and stars
python nombrar.py                           # topic names (needs Ollama)
python gen_mapa3d.py                        # -> universo3d.html
```

Raw texts, vectors and generated pages are not in git; they are rebuilt by the pipeline. The
*Attention* paper and its translations are not included (copyright). Download it from
arXiv:1706.03762 to rerun the control. The LLM judge is called through an API key read from `.env`,
which is not in the repository.

## Sources

Project Gutenberg (public domain); Hegel, *Grundlinien der Philosophie des Rechts* (Zeno.org TEI);
S. W. Dyde, *Philosophy of Right* (1896, Cornell OCR).
