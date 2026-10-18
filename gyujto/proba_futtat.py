#!/usr/bin/env python3
# Próbafutás (forras-proba ág): csak a három új forrás, az eredmény a proba/ mappába.
import json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import gyujt  # noqa: E402
ki = []
for nev, f in [('PÁRIZS', gyujt.paris), ('NANTES', gyujt.nantes), ('AMIENS', gyujt.amiens)]:
    t = time.time()
    try:
        r = f()
        ki.append(f'== {nev}: {len(r)} tétel ({round(time.time() - t)} mp), átnézve: {gyujt.ATNEZVE.get(nev.lower().replace("á", "a"))}')
        for m in r:
            ki.append('  ' + json.dumps(m, ensure_ascii=False))
    except Exception as e:
        import traceback
        ki.append(f'== {nev}: HIBA {e}\n' + traceback.format_exc()[-1500:])
os.makedirs('proba', exist_ok=True)
open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
print('\n'.join(ki))
