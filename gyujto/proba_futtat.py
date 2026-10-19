#!/usr/bin/env python3
# Felderítés: jegy.hu, interticket, BBC Radio 4 Extra, ARTE, Operabase, Cinémathèque française.
import os, sys, re, json, datetime as dt, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
import gyujt  # noqa: E402
ki = []
def ir(*a): ki.append(' '.join(str(x) for x in a))
def lek(url, ny='hu'):
    try:
        return gyujt.letolt(url, ny, 40).decode('utf-8', 'replace')
    except Exception as e:
        ir('  HIBA', url, str(e)[:120]); return ''
def kivonat(nev, h, minta=r'(?i)verne|nemo|80 nap|f[öo]ld k[öo]r[üu]l|20 ?000|h[uú]szezer|rejtelmes sziget|strogof'):
    ir(f'== {nev}: {len(h)} bájt, találat-szavak: {len(re.findall(minta, h))}')
    for m in list(re.finditer(minta, h))[:12]:
        ir('   …', gyujt.szoveg(h[max(0, m.start() - 160): m.end() + 160])[:260])
    for l in list(dict.fromkeys(re.findall(r'href="([^"]+)"', h)))[:0]: ir('   L', l)
# 1. magyar jegyrendszerek
for u in ['https://jegy.hu/search?q=verne', 'https://jegy.hu/search?q=80+nap', 'https://jegy.hu/search?q=nemo+kapit%C3%A1ny',
          'https://www.interticket.hu/kereses?q=verne', 'https://www.interticket.hu/search?q=verne']:
    kivonat(u, lek(u))
# 2. BBC Radio 4 Extra
for nap in range(0, 3):
    d = (dt.date.today() + dt.timedelta(days=nap)).isoformat()
    u = f'https://rms.api.bbc.co.uk/v2/experience/inline/schedules/bbc_radio_four_extra/{d}'
    h = lek(u, 'en')
    ir(f'== BBC R4X {d}: {len(h)} bájt', h[:200].replace('\n', ' '))
    if h:
        try:
            dd = json.loads(h)
            cimek = re.findall(r'"primary":"([^"]+)","secondary":"([^"]*)"', h)
            ir('   címek:', ' ¦ '.join(f'{a} – {b}' for a, b in cimek[:40])[:1500])
        except Exception as e:
            ir('   json hiba', e)
h = lek('https://www.bbc.co.uk/sounds/search?q=jules%20verne', 'en'); kivonat('BBC Sounds keresés', h)
# 3. ARTE
for u in ['https://www.arte.tv/api/rproxy/emac/v4/fr/web/pages/SEARCH/?query=jules%20verne',
          'https://www.arte.tv/api/rproxy/emac/v4/de/web/pages/SEARCH/?query=jules%20verne',
          'https://www.arte.tv/fr/search/?q=jules%20verne']:
    h = lek(u, 'fr'); kivonat(u, h)
# 4. Operabase
for u in ['https://www.operabase.com/search?q=voyage%20dans%20la%20lune', 'https://www.operabase.com/works/le-voyage-dans-la-lune-5378/performances',
          'https://www.operabase.com/en/search?query=offenbach%20voyage']:
    h = lek(u, 'en'); kivonat(u, h, r'(?i)voyage dans la lune|docteur ox|reise in den mond|viaggio nella luna|trip to the moon')
# 5. Cinémathèque
for u in ['https://www.cinematheque.fr/recherche.html?q=jules+verne', 'https://www.cinematheque.fr/cycle/', 'https://www.cinematheque.fr/']:
    h = lek(u, 'fr'); kivonat(u, h, r'(?i)verne|m[ée]li[èe]s|zeman')
os.makedirs('proba', exist_ok=True)
open('proba/osszegzes.txt', 'w', encoding='utf-8').write('\n'.join(ki) + '\n')
