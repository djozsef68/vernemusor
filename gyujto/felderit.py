#!/usr/bin/env python3
# Felderítés, 5. kör: Amiens – egy eseménykártya szerkezete a fő listán, és a lapozás.
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from gyujt import letolt, szoveg  # noqa: E402
ki = []
def ir(*a): ki.append(' '.join(str(x) for x in a))
def lek(url):
    try:
        return letolt(url, 'fr', 40).decode('utf-8', 'replace')
    except Exception as e:
        ir('HIBA', url, str(e)[:200]); return ''
h = lek('https://www.amiens.fr/Les-evenements')
linkek = list(dict.fromkeys(l for l in re.findall(r'href="(/Les-evenements/[^"(#]+)"', h)))
ir('linkek:', len(linkek), linkek[:12])
if linkek:
    i = h.find('href="' + linkek[0])
    ir('KÁRTYA nyers:', re.sub(r'\s+', ' ', h[max(0, i - 2500): i + 600]))
for p in list(dict.fromkeys(re.findall(r'href="([^"]*(?:\(offset\)|\(page\)|page=|offset=)[^"]*)"', h)))[:8]: ir('lapozó:', p)
ir('találatszám-szöveg:', ' ¦ '.join(re.findall(r'(?i)[^<>]{0,40}\d+\s+(?:événements?|résultats?)[^<>]{0,40}', h))[:300])
open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
