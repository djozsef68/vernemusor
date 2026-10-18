#!/usr/bin/env python3
# Felderítés, 4. kör: Amiens – honnan tölti a lista az eseményeket?
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from gyujt import letolt, szoveg  # noqa: E402
ki = []
def ir(*a): ki.append(' '.join(str(x) for x in a))
def lek(url):
    try:
        return letolt(url, 'fr', 40).decode('utf-8', 'replace')
    except Exception as e:
        ir('HIBA', url, str(e)[:200]); return ''
h = lek('https://www.amiens.fr/Les-evenements/(organisateur)/maison-de-jules-verne')
for p in sorted(set(re.findall(r'(?i)(?:data-[a-z-]*(?:url|src|endpoint|api)[a-z-]*|action)="([^"]{4,200})"', h)))[:40]: ir('  data-url:', p)
for p in sorted(set(re.findall(r'(?i)["\'](/[^"\' ]*(?:ajax|api|json|layout/set|ezjscore|events?)[^"\' ]*)["\']', h)))[:40]: ir('  út:', p)
for s in re.findall(r'(?s)<script[^>]*src="([^"]+)"', h)[:30]: ir('  szkript:', s)
i = h.find('events__list')
ir('  LISTA környezet:', re.sub(r'\s+', ' ', h[i:i + 3000])[:2500])
ir('  "Verne" előfordulások:', ' ¦ '.join(re.sub(r'\s+', ' ', h[max(0, m.start() - 120):m.end() + 120]) for m in re.finditer(r'(?i)verne', h))[:3000])
open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
