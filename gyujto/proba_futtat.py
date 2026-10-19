#!/usr/bin/env python3
# Felderítés 3: a jegy.hu programBox szerkezete; az ARTE oldalon hol vannak az adatok.
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import gyujt  # noqa: E402
ki = []
def ir(*a): ki.append(' '.join(str(x) for x in a))
h = gyujt.letolt('https://jegy.hu/search?q=80+nap', 'hu').decode('utf-8', 'replace')
dobozok = h.split('class="programBox')[1:]
ir('JEGY dobozok:', len(dobozok))
for d in dobozok[:3]:
    ir('JEGY doboz:', re.sub(r'\s+', ' ', d[:1800]))
a = gyujt.letolt('https://www.arte.tv/fr/search/?q=jules%20verne', 'fr').decode('utf-8', 'replace')
ir('ARTE scriptek:', ' | '.join(re.findall(r'<script[^>]*(?:id|type)="([^"]+)"', a))[:600])
for m in list(re.finditer(r'Verne', a))[3:9]:
    ir('ARTE környezet:', re.sub(r'\s+', ' ', a[max(0, m.start() - 600): m.end() + 600]))
os.makedirs('proba', exist_ok=True)
open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
