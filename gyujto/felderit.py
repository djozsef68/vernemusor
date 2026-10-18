#!/usr/bin/env python3
# Felderítés, 2. kör: Nantes nyílt adat mezői és rekordjai; Amiens – a Maison de Jules Verne szervezői oldala.
import json, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from gyujt import letolt, szoveg  # noqa: E402
Q = urllib.parse.quote
ki = []
def ir(*a): ki.append(' '.join(str(x) for x in a))
def lek(url):
    try:
        return letolt(url, 'fr', 40).decode('utf-8', 'replace')
    except Exception as e:
        ir('HIBA', url, str(e)[:200]); return ''
B = 'https://data.nantesmetropole.fr/api/explore/v2.1/catalog/datasets/244400404_agenda-evenements-nantes-metropole_v2'
m = lek(B)
if m:
    ir('NANTES mezők:', ', '.join(f['name'] for f in json.loads(m).get('fields', [])))
r = lek(B + '/records?where=' + Q('search("jules verne")') + '&limit=30&order_by=date')
if r:
    d = json.loads(r); ir('NANTES találat:', d.get('total_count'))
    for x in d.get('results', []):
        ir('  N|', json.dumps(x, ensure_ascii=False)[:900])
h = lek('https://www.amiens.fr/Les-evenements/(organisateur)/maison-de-jules-verne')
if h:
    ir('AMIENS MJV', len(h))
    i = h.find('Les-evenements/', h.find('maison-de-jules-verne') + 200)
    for l, t in re.findall(r'<a[^>]+href="(/Les-evenements/[A-Za-z0-9][^"(#]+)"[^>]*>(.*?)</a>', h, re.S)[:40]:
        ir('  A|', l, '|', szoveg(t)[:140])
    # egy esemény-kártya nyers szerkezete (címkék nélkül, csak a szövege és az osztálynevek)
    k = re.search(r'(?s)(<(?:article|li|div)[^>]*class="[^"]*(?:event|agenda|card)[^"]*"[^>]*>.{0,2500})', h)
    if k:
        ir('  KÁRTYA osztályok:', ' '.join(sorted(set(re.findall(r'class="([^"]+)"', k.group(1)))))[:800])
        ir('  KÁRTYA szöveg:', szoveg(k.group(1))[:600])
    for p in re.findall(r'href="([^"]*(?:page|offset)[^"]*)"', h)[:5]: ir('  lapozó:', p)
    if 'Les-evenements/' in h:
        l0 = re.findall(r'href="(/Les-evenements/[A-Za-z0-9][^"(#]+)"', h)
        if l0:
            e = lek('https://www.amiens.fr' + l0[0])
            if e:
                ir('  ESEMÉNY-OLDAL', l0[0], 'szöveg:', szoveg(re.sub(r'(?s)<(header|nav|footer)[^>]*>.*?</\1>', ' ', e))[:900])
                for d in re.findall(r'(?is)<time[^>]*>.*?</time>|datetime="[^"]+"|class="[^"]*date[^"]*"[^>]*>[^<]{0,80}', e)[:8]: ir('  dátumjel:', szoveg(d)[:160], d[:120])
open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
print('\n'.join(ki))
