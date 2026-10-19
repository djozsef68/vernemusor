#!/usr/bin/env python3
# Próba: jegy.hu, BBC rádió, ARTE.
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import gyujt  # noqa: E402
ki = []
for nev, f in [('ARTE', gyujt.arte)]:
    try:
        r = f()
        ki.append(f'== {nev}: {len(r)} (átnézve: {gyujt.ATNEZVE.get(nev.lower())})')
        for m in r: ki.append('   ' + json.dumps(m, ensure_ascii=False)[:330])
    except Exception as e:
        import traceback; ki.append(f'== {nev}: HIBA {e} ' + traceback.format_exc()[-600:])
os.makedirs('proba', exist_ok=True)
open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
