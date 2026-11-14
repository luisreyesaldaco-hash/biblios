"""Baja el canon de Gutenberg a fuentes/gutenberg/txt/ (idempotente, 1 s entre libros)."""
import os, time, urllib.request
from canon import CANON
DST = os.path.join(os.path.dirname(__file__), '..', 'fuentes', 'gutenberg', 'txt')
os.makedirs(DST, exist_ok=True)
for autor, ids in CANON.items():
    for i in ids:
        p = os.path.join(DST, f'{i}.txt')
        if os.path.exists(p) and os.path.getsize(p) > 1000: continue
        url = f'https://www.gutenberg.org/cache/epub/{i}/pg{i}.txt'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'biblios-research/0.1'})
            data = urllib.request.urlopen(req, timeout=60).read()
            open(p, 'wb').write(data)
            first = data[:2000].decode('utf-8', 'ignore')
            t = next((l for l in first.splitlines() if l.startswith('Title:')), '?')
            print(f'OK  {autor:16} {i:6} {len(data)//1024:6} KB  {t}')
        except Exception as e:
            print(f'ERR {autor:16} {i:6} {e}')
        time.sleep(1)
