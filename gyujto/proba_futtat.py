#!/usr/bin/env python3
# Próbafutás (forras-proba ág): cseh, szlovák, román, horvát, szerb tévé- és rádióműsor (epgshare01) – elérhető-e, hoz-e Verne-tételt.
import json, os, sys, time, re, gzip, io
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(__file__))
import gyujt  # noqa: E402
ki = []
for orszag, cimkek in [('cz', ['CZ1', 'CZ2']), ('sk', ['SK1', 'SK2']), ('ro', ['RO1', 'RO2']), ('hr', ['HR1', 'HR2']), ('rs', ['RS1', 'RS2'])]:
    for c in cimkek:
        t = time.time()
        try:
            adat = gyujt.letolt(f'https://epgshare01.online/epgshare01/epg_ripper_{c}.xml.gz', 'hu', ido=300)
        except Exception as e:
            ki.append(f'== {c}: nem érhető el ({str(e)[:80]})'); continue
        csat, prog, napok = set(), 0, set()
        for _, e in ET.iterparse(io.BytesIO(adat), events=('end',)):
            if e.tag == 'channel':
                csat.add((e.findtext('display-name') or '').strip()); e.clear()
            elif e.tag == 'programme':
                prog += 1; napok.add((e.get('start') or '')[:8]); e.clear()
        try:
            r = gyujt.epg_orszag(orszag, c)
        except Exception as e:
            ki.append(f'== {c}: feldolgozási hiba {e}'); continue
        ki.append(f'== {c}: {len(csat)} csatorna, {prog} műsor, {len(napok)} nap ({min(napok) if napok else "-"}–{max(napok) if napok else "-"}), Verne: {len(r)} ({round(time.time()-t)} mp)')
        ki.append('   csatornák: ' + ', '.join(sorted(csat))[:900])
        for m in r:
            ki.append(f"   {m['tipus']} {m['kezd'][:16]} {m['csatorna']} | {m['cim']} | {m.get('alcim','')[:60]} | {m['orszag']}")
os.makedirs('proba', exist_ok=True)
open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
print('\n'.join(ki))
