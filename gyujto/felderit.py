#!/usr/bin/env python3
# Felderítés, 3. kör: Amiens – a Maison de Jules Verne eseménylistájának szerkezete; Nantes – a dátummezők.
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
r = lek(B + '/records?where=' + Q('search("jules verne") and date >= date\'2026-10-18\'') + '&limit=5&order_by=date&select=id_manif,nom,date,heure_debut,heure_fin,lieu,adresse,ville,emetteur,types_libelles,url_site,lien_agenda')
if r:
    d = json.loads(r); ir('NANTES jövő:', d.get('total_count'))
    for x in d.get('results', []): ir('  N|', json.dumps(x, ensure_ascii=False)[:500])
h = lek('https://www.amiens.fr/Les-evenements/(organisateur)/maison-de-jules-verne')
if h:
    linkek = []
    for l in re.findall(r'href="([^"]*Les-evenements/[^"]+)"', h):
        if '(' not in l and l not in linkek: linkek.append(l)
    ir('AMIENS MJV linkek:', len(linkek))
    for l in linkek[:30]: ir('  L|', l)
    if linkek:
        i = h.find(linkek[0])
        blokk = h[max(0, i - 1500): i + 1500]
        ir('  KÖRNYEZET szöveg:', szoveg(blokk)[:700])
        ir('  KÖRNYEZET osztályok:', ' | '.join(dict.fromkeys(c.strip() for c in re.findall(r'class="([^"]+)"', blokk)))[:900])
        e = lek(linkek[0] if linkek[0].startswith('http') else 'https://www.amiens.fr' + linkek[0])
        if e:
            t = re.sub(r'(?s)<(header|nav|footer|script|style)[^>]*>.*?</\1>', ' ', e)
            j = t.find('<h1')
            ir('  ESEMÉNY szöveg:', szoveg(t[j:j + 5000])[:900])
            for c in dict.fromkeys(re.findall(r'class="([^"]*(?:date|hour|time|place|lieu|horaire)[^"]*)"', t)): ir('  osztály:', c[:120])
open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
print('\n'.join(ki))
