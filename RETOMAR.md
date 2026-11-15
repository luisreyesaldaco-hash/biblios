# RETOMAR — biblios

## Estado (14-nov-2026)
- Universo v1: **52 filósofos, 102 obras, 16,277 pasajes**, de los presocráticos a Russell.
  Mapas 2D y 3D publicados (ligas en `CLAUDE.md`); el 3D tiene modo por obra (sub-nebulosas,
  amplitud y matriz de distancias entre obras de un autor). Excel en `atlas/universo.xlsx`.
- Hallazgos: estoicos juntos; Kant–Hegel–Schopenhauer; Peirce–Russell es el par más cercano (0.008);
  Oriente (Lao Tse, Confucio, Zhuangzi) forma su nebulosa y Confucio es el "más lejano" de casi todos;
  Plotino junto a Hegel y Tomás; Grocio junto a Rousseau/Aristóteles/Mill (nebulosa del derecho).
  Dentro de autores: Platón, Aristóteles y Kant son los más "amplios"; Hegel el más compacto.
- Faltan (no están en Gutenberg o tienen derechos): Wittgenstein, Hegel *Fenomenología*, Fichte,
  Husserl, Frege, Heráclito/Epicuro sueltos, filósofos en español.

## Siguientes pasos posibles
1. Quitar ruido de estilo/traductor antes de leer tesis (p. ej. restar la componente "voz" o comparar
   solo dentro de una misma época/traductor).
2. Lo caro: descomponer un tema en preguntas atómicas (¿ideas innatas?, ¿mundo externo?, ¿certeza?)
   y que cada filósofo responda sí/no/calla con `@ref`. Ahí sí aparecen tesis, antítesis y lagunas.
   Los embeddings sirven para *encontrar* los pasajes que contestan cada pregunta.
3. Primer ensayo de quaestio: mentir para salvar una vida (Kant vs. Constant 1797, Tomás II-II q.110).
4. Nombre de la familia de lenguajes (pendiente, decide Luis).

## 15-nov-2026 — Jev, Platón por orador y la nebulosa que colapsa
- **Jev funciona** (`TYPESAFE_API_KEY` en `.env`, `jev-latest` = jev-1.14.0). Control de negación perfecto; ideas innatas
  5/6 a ciegas leyendo 10 pasajes juntos (NLI 3/6). Nunca darle el nombre del autor (sube a 6/6 por memoria).
- **`oradores/`**: Platón completo (29 diálogos Jowett) dividido por orador → 19,322 turnos, 72 voces.
  Dramáticos por rótulo; narrados por reglas + Jev con contexto (~$0.28); Parménides II por alternancia cerrada.
  Revisión a mano: República 8/8; Cármides: Jev 8/10 vs. alternancia 1/10. Faltan las Cartas (no están en Jowett/Gutenberg).
- **Colapso** (`colapso.py`, en Newton): e5 → UMAP 10D → HDBSCAN: 21 galaxias, 85 estrellas con sentido
  (caverna, Diotima, Atlántida, auriga, Trasímaco…). La reminiscencia cae dentro de la inmortalidad (Fedón).
- **Postura por orador** (`postura_estrella.py`): estrella 16 contra la tesis de Trasímaco → Sócrates 0/69, Trasímaco 14/0,
  Calicles a favor. Con contexto previo es indispensable. Pendiente: Glaucón sale "a favor" (11) cuando hace de abogado
  del diablo (libro II): la voz no es la creencia.
- **Siguiente:** mapa visual de las estrellas; que Luis escriba/elija tesis por estrella; examen común con soporte (OK pendiente).
