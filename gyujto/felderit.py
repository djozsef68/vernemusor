#!/usr/bin/env python3
# Egyszeri felderítés (forras-proba ág): a három új forrás válaszaiból kivonatot ír a proba/ mappába
# (nyers HTML-t nem ment – abban a GitHub titoknak vélt kulcsokat talál).
import json, os, re, sys, html, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from gyujt import letolt, szoveg  # noqa: E402

Q = urllib.parse.quote
os.makedirs('proba', exist_ok=True)
ki = []
def ir(*a): ki.append(' '.join(str(x) for x in a))
def lek(url):
    try:
        return letolt(url, 'fr', 40).decode('utf-8', 'replace')
    except Exception as e:
        ir('HIBA', url, str(e)[:150]); return ''

# Párizs
m = lek('https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-')
if m:
    d = json.loads(m); ir('PÁRIZS mezők:', ', '.join(f['name'] for f in d.get('fields', [])))
r = lek('https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-/records?where=' + Q('search("jules verne")') + '&limit=20')
if r:
    d = json.loads(r); ir('PÁRIZS találat:', d.get('total_count'))
    for x in d.get('results', []):
        ir('  P|', x.get('title'), '|', x.get('date_start'), '→', x.get('date_end'), '|', x.get('address_name'), '|', x.get('address_city'), '|', x.get('url'), '|', str(x.get('occurrences'))[:160], '|', str(x.get('date_description'))[:200].replace('\n', ' '))

# Nantes
k = lek('https://data.nantesmetropole.fr/api/explore/v2.1/catalog/datasets?where=' + Q('search("agenda")') + '&limit=30')
if k:
    try:
        for x in json.loads(k).get('results', []):
            ir('  NK|', x.get('dataset_id'), '|', (x.get('metas', {}).get('default', {}) or {}).get('title'), '|', ', '.join(f['name'] for f in x.get('fields', []))[:400])
    except Exception as e:
        ir('NK hiba', e)
for nev, url in [('NANTES agenda', 'https://metropole.nantes.fr/que-faire-a-nantes/agenda'),
                 ('NANTES agenda keresés', 'https://metropole.nantes.fr/que-faire-a-nantes/agenda?search_api_fulltext=jules+verne'),
                 ('NANTES keresés', 'https://metropole.nantes.fr/recherche?search_api_fulltext=jules+verne')]:
    h = lek(url)
    if not h: continue
    ir(nev, len(h), 'verne-előfordulás:', len(re.findall(r'(?i)verne', h)))
    for l, t in re.findall(r'<a[^>]+href="(/que-faire-a-nantes/agenda/[^"#?]+)"[^>]*>(.*?)</a>', h, re.S)[:40]:
        ir('  N|', l, '|', szoveg(t)[:120])
    for f in re.findall(r'<form[^>]*>', h)[:5]: ir('  űrlap:', f[:200])
    for i in re.findall(r'<input[^>]*name="[^"]+"[^>]*>', h)[:15]: ir('  mező:', i[:160])

# Amiens
for nev, url in [('AMIENS események', 'https://www.amiens.fr/Les-evenements'),
                 ('AMIENS keresés', 'https://www.amiens.fr/content/search?SearchText=Jules+Verne')]:
    h = lek(url)
    if not h: continue
    ir(nev, len(h), 'verne-előfordulás:', len(re.findall(r'(?i)verne', h)))
    for l, t in re.findall(r'<a[^>]+href="([^"]*Les-evenements/[^"#]+)"[^>]*>(.*?)</a>', h, re.S)[:60]:
        ir('  A|', l, '|', szoveg(t)[:120])
    for f in re.findall(r'<form[^>]*>', h)[:5]: ir('  űrlap:', f[:200])
    for i in re.findall(r'<(?:input|select)[^>]*name="[^"]+"[^>]*>', h)[:20]: ir('  mező:', i[:160])
    for d in re.findall(r'(?i)[^<>]{0,80}\d{1,2}\s+(?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[^<>]{0,60}', h)[:10]: ir('  dátum:', szoveg(d)[:140])

open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
print('\n'.join(ki))
