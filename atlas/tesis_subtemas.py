"""Nombre y tesis discutible de cada subtema, con qwen2.5:32b local (Newton, $0). La tesis es un BORRADOR para que Luis la revise.
Uso (Newton): python3 tesis_subtemas.py subtemas_g11.json  -> tesis_g11.json"""
import json, sys, re, urllib.request
ENT = sys.argv[1]; SAL = ENT.replace('subtemas_', 'tesis_')
S = json.load(open(ENT))
PROMPT = """You are helping build a map of philosophy. Below are passages from different philosophers that a clustering algorithm grouped together as one specific topic, plus its most distinctive words.

Distinctive words: {palabras}

Passages:
{pasajes}

Do three things:
1. "nombre": a short Spanish (es-MX) title of 3 to 6 words naming the specific topic.
2. "tesis": ONE precise, contestable philosophical proposition in English, about this topic, on which these philosophers would plausibly DISAGREE (some would affirm it, others deny it). One sentence, a claim (not a question), no names of philosophers.
3. "tesis_es": the same proposition in Spanish (es-MX).
4. "nucleo": in English, the specific question the proposition decides (one line, starting with "whether").

Answer ONLY with a JSON object with the keys nombre, tesis, tesis_es, nucleo."""

def qwen(p):
    req = urllib.request.Request('http://localhost:11434/api/generate', data=json.dumps({
        'model': 'qwen2.5:32b', 'prompt': p, 'stream': False, 'format': 'json',
        'options': {'temperature': 0.2, 'num_ctx': 8192, 'seed': 42}}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=1800) as r: return json.loads(json.load(r)['response'])

out = []
for k, s in enumerate(S, 1):
    p = PROMPT.format(palabras=', '.join(s['palabras']), pasajes='\n\n'.join(f'- {c["texto"]}' for c in s['centrales']))
    r = qwen(p); r['id'] = s['id']; out.append(r)
    print(f'{k}/{len(S)} {s["id"]}: {r.get("nombre")} | {r.get("tesis")}', flush=True)
    json.dump(out, open(SAL, 'w'), ensure_ascii=False, indent=1)
print('FIN', SAL, flush=True)
