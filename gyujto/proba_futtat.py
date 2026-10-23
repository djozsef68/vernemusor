# Forráspróba: magyar Wikipédia nyers wikiszöveg (action=raw), átirányítást egyszer követve; teljes szöveg mentése.
import json, os, re, urllib.request, urllib.parse
UA = {'User-Agent': 'Nautilus-forraspróba/1.0 (nautilus.djp.hu; kapcsolat a weboldalon)'}
U = json.load(open('gyujto/proba_urls.json'))
os.makedirs('proba', exist_ok=True)
ossz = []
def raw(cim):
    u = 'https://hu.wikipedia.org/w/index.php?title=' + urllib.parse.quote(cim.replace(' ', '_')) + '&action=raw'
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45).read().decode('utf-8', 'replace')
for k, cim in U.items():
    try:
        t = raw(cim)
        m = re.match(r'#(?:ÁTIRÁNYÍTÁS|REDIRECT)\s*\[\[([^\]]+)\]\]', t, re.I)
        if m:
            t = raw(m.group(1))
        open(f'proba/{k}.txt', 'w').write(t)
        ossz.append(f'{k} | {cim} | {len(t)} karakter')
    except Exception as e:
        ossz.append(f'{k} | {cim} | HIBA {e}')
open('proba/osszegzes.txt', 'w').write('\n'.join(ossz) + '\n')
