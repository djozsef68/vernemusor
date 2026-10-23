# Forráspróba: antikvarium.hu – Verne magyar kiadásai (találati lapok + részletlapok), udvarias tempóban.
import json, os, re, html, time, urllib.request, urllib.parse, concurrent.futures as cf
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36', 'Accept-Language': 'hu'}
B = 'https://www.antikvarium.hu/'
def get(u, n=3):
    for i in range(n):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode('utf-8', 'replace')
        except Exception as e:
            err = e; time.sleep(3 + 5 * i)
    raise err
os.makedirs('proba', exist_ok=True)
linkek = {}
for q in ['verne gyula', 'jules verne']:
    lap = 1
    while lap < 60:
        s = get(B + 'index.php?type=search&ksz=' + urllib.parse.quote_plus(q) + ('&oldalcount=%d' % lap if lap > 1 else ''))
        uj = re.findall(r'href="konyv/([^"]+)"', s)
        for x in uj:
            m = re.search(r'-(\d+)-\d+$', x)
            if m:
                linkek.setdefault(m.group(1), x)
        if not uj or ('oldalcount=%d' % (lap + 1)) not in s:
            break
        lap += 1; time.sleep(0.6)
def txt(s):
    t = re.sub(r'(?is)<(script|style).*?</\1>', ' ', s)
    return [x.strip() for x in html.unescape(re.sub(r'<[^>]+>', '\n', t)).splitlines() if x.strip()]
def mezo(L, cimke):
    for i, x in enumerate(L):
        if x.rstrip(':') == cimke and i + 1 < len(L):
            return L[i + 1]
    return ''
def egy(kv):
    kid, slug = kv
    try:
        s = get(B + 'konyv/' + slug); L = txt(s)
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S)
        ford = []
        for i, x in enumerate(L):
            if x in ('Fordító', 'Fordítók') and i + 1 < len(L):
                ford.append(L[i + 1])
        r = {'id': kid, 'url': B + 'konyv/' + slug, 'cim': html.unescape(re.sub(r'<[^>]+>', '', h1.group(1))).strip() if h1 else '',
             'kiado': mezo(L, 'Kiadó'), 'hely': mezo(L, 'Kiadás helye'), 'ev': mezo(L, 'Kiadás éve'), 'fordito': ford,
             'oldal': mezo(L, 'Oldalszám'), 'sorozat': mezo(L, 'Sorozatcím'), 'kotet': mezo(L, 'Kötetszám'), 'kiadas': mezo(L, 'Kiadás'),
             'nyelv': mezo(L, 'Nyelv'), 'isbn': mezo(L, 'ISBN')}
        m = re.search(r'Szerző[^<]{0,40}</[^>]+>\s*<[^>]+>([^<]+)', s)
        time.sleep(0.4)
        return r
    except Exception as e:
        return {'id': kid, 'url': B + 'konyv/' + slug, 'hiba': str(e)}
with cf.ThreadPoolExecutor(3) as ex:
    res = list(ex.map(egy, linkek.items()))
with open('proba/antikvarium.jsonl', 'w') as f:
    for r in res:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
open('proba/osszegzes.txt', 'w').write('linkek: %d, részletlap: %d, hiba: %d\n' % (len(linkek), len(res), sum(1 for r in res if 'hiba' in r)))
