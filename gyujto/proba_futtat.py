#!/usr/bin/env python3
# Felderítés 2: a jegy.hu találatlista és az ARTE keresés szerkezete.
import os, sys, re, json
sys.path.insert(0, os.path.dirname(__file__))
import gyujt  # noqa: E402
ki = []
def ir(*a): ki.append(' '.join(str(x) for x in a))
h = gyujt.letolt('https://jegy.hu/search?q=80+nap', 'hu').decode('utf-8', 'replace')
linkek = list(dict.fromkeys(re.findall(r'href="(/(?:program|event|esemeny|eloadas)[^"#]*)"', h)))
ir('JEGY linkek:', len(linkek), linkek[:15])
for l in linkek[:2]:
    i = h.find(l)
    ir('JEGY környezet:', re.sub(r'\s+', ' ', h[max(0, i - 1500): i + 1500]))
ir('JEGY osztályok:', ' | '.join(list(dict.fromkeys(re.findall(r'class="([^"]*(?:result|card|item|program|event)[^"]*)"', h)))[:40]))
if linkek:
    e = gyujt.letolt('https://jegy.hu' + linkek[0], 'hu').decode('utf-8', 'replace')
    ir('JEGY adatlap ld+json:', ' ¦ '.join(x[:700] for x in re.findall(r'(?s)<script type="application/ld\+json">(.*?)</script>', e))[:2500])
a = gyujt.letolt('https://www.arte.tv/fr/search/?q=jules%20verne', 'fr').decode('utf-8', 'replace')
m = re.search(r'(?s)<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', a)
ir('ARTE NEXT_DATA:', bool(m), len(m.group(1)) if m else 0)
if m:
    t = m.group(1)
    for x in re.finditer(r'"title":"([^"]{3,120})","subtitle":(null|"[^"]*")', t):
        ir('  A', x.group(1), '|', x.group(2)[:80])
    i = t.find('Verne')
    ir('ARTE nyers:', t[max(0, i - 1500): i + 1500])
os.makedirs('proba', exist_ok=True)
open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
