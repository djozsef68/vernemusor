#!/usr/bin/env python3
# Egyszeri felderítés (forras-proba ág): a három új forrás nyers válaszait a proba/ mappába menti.
import os, sys, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from gyujt import letolt  # noqa: E402

Q = urllib.parse.quote
celok = {
    'paris_rekordok.json': 'https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-/records?where=' + Q('search("jules verne")') + '&limit=20',
    'paris_mezok.json': 'https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-',
    'nantes_katalogus.json': 'https://data.nantesmetropole.fr/api/explore/v2.1/catalog/datasets?where=' + Q('search("agenda")') + '&limit=30&select=dataset_id,metas',
    'nantes_agenda.html': 'https://metropole.nantes.fr/que-faire-a-nantes/agenda',
    'nantes_kereses.html': 'https://metropole.nantes.fr/que-faire-a-nantes/agenda?search_api_fulltext=jules+verne',
    'nantes_kereses2.html': 'https://metropole.nantes.fr/recherche?search_api_fulltext=jules+verne',
    'amiens_esemenyek.html': 'https://www.amiens.fr/Les-evenements',
    'amiens_kereses.html': 'https://www.amiens.fr/Recherche?SearchText=Jules+Verne',
    'amiens_kereses2.html': 'https://www.amiens.fr/content/search?SearchText=Jules+Verne',
}
os.makedirs('proba', exist_ok=True)
with open('proba/osszegzes.txt', 'w', encoding='utf-8') as o:
    for nev, url in celok.items():
        try:
            adat = letolt(url, 'fr', 40)
            open('proba/' + nev, 'wb').write(adat[:1500000])
            o.write(f'OK   {nev} {len(adat)} bájt  {url}\n')
        except Exception as e:
            o.write(f'HIBA {nev} {str(e)[:150]}  {url}\n')
print(open('proba/osszegzes.txt', encoding='utf-8').read())
