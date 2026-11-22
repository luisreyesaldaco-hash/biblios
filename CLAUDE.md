# biblios — el universo de la filosofía

Proyecto de Luis Reyes Aldaco (lab, no producción). Hermano de Knst (`~/lab/knst`): así como Knst
carga el **derecho** con lógica deóntica, biblios mapea **toda la filosofía**, primero barato
(embeddings: dónde se acercan y alejan las ideas) y después caro (leer tesis: quién afirma o niega qué).

**Al entrar: lee `RETOMAR.md`.**

## Decisiones tomadas (13–14 nov 2026, con Luis)
- **Primero el mapa, después las tesis.** Mapear (scrapear + embeddings) es barato; leer o traducir
  tesis es lo caro. El mapa va primero.
- **Cada rama de la filosofía tendrá su propio lenguaje** (dialecto de un núcleo común con Knst):
  ver `MAPA.md`. El nombre de la familia de lenguajes está pendiente (Luis lo decide).
- **Un solo idioma en el corpus** (traducciones inglesas de dominio público): si se mezclan idiomas,
  las nebulosas se agrupan por idioma y no por ideas.
- **Muestreo parejo por obra** (tope 350 pasajes por autor, repartido entre sus obras), para que una obra
  larga no defina al autor (caso Zaratustra).
- Inspiración: el feature **Atlas** de LegalAtlas (`~/legalatlas/api/atlas.js`, tesis/antítesis).

## Límite conocido (no olvidar)
Los embeddings miden **de qué se habla, no qué se afirma**: "X" y "no X" quedan casi idénticos
(control en `atlas/gnoseologia.py`: 0.039 vs 0.207 de otro tema). Cercanía = mismo territorio temático,
no acuerdo. También pesan el **estilo** (verso, inglés de 1651) y el **traductor**.

## Estructura
- `MAPA.md` — ramas de la filosofía → lógica de base → operadores → madurez formal.
- `fuentes/gutenberg/` — catálogo y textos de Project Gutenberg (ignorados en git; se re-bajan).
- `atlas/` — el pipeline del universo:
  `canon.py` (autores→IDs Gutenberg, orden cronológico) → `bajar.py` → `pasajes.py` → `embeber.py`
  (en Newton) → `gen_mapa.py` / `gen_mapa3d.py` (sobre `*_tpl.html`).

## Cómo correr (orden)
```bash
cd ~/lab/biblios/atlas
python3 bajar.py            # idempotente, 1 s entre libros
python3 pasajes.py          # -> pasajes.json
# embeddings: SIEMPRE en Newton Max (DEMIAN es producción; en DEMIAN tardó ~9 h y ahogó el server)
scp pasajes.json embeber.py newton-max:biblios-atlas/
ssh newton-max 'cd ~/biblios-atlas && nohup .venv/bin/python embeber.py > embeber.log 2>&1 &'
# reutiliza vectores de cache_pasajes.json/cache_vectores.npy si existen (renombrar los anteriores)
scp newton-max:biblios-atlas/{vectores.npy,mapa2d.npy,mapa3d.npy,universo.xlsx} .
~/lab/bench-emb-venv/bin/python gen_mapa.py && ~/lab/bench-emb-venv/bin/python gen_mapa3d.py
```
- Modelo: `intfloat/multilingual-e5-large`, local (costo de API: $0). Prefijo `passage: `.
- En DEMIAN, `~/lab/bench-emb-venv` tiene numpy/sklearn/openpyxl para generar las páginas.
- En Newton, `~/biblios-atlas/.venv` (uv, Python 3.12, torch con MPS).

## Publicado (artifacts privados de Luis)
- 3D: https://claude.ai/artifact/7HWLpU3Kgbsf95wi8oRwRY  (`atlas/universo3d.html`)
- 2D: https://claude.ai/artifact/2caufiuCbigSbZAdtW9Svq  (`atlas/universo.html`)
Para actualizar: regenerar el html y republicar el mismo archivo (misma URL).

## Reglas
- **Repo PÚBLICO** desde el 22-nov-2026: https://github.com/luisreyesaldaco-hash/biblios (rama `main`). Todo commit se vuelve público al hacer push: nada con derechos (p. ej. el PDF de Attention), ni secretos, ni notas privadas. Datos grandes fuera de git (`.gitignore`).
- Solo textos de dominio público en `fuentes/`.
- La filosofía es de Luis; la herramienta mapea y diagnostica, no escribe su sistema.
