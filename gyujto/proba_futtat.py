# Forráspróba: a névadó-jelöltek ellenőrzése – Wikipédia (keresés + bevezető + koordináta) és OpenStreetMap (Nominatim).
import json, os, time, urllib.request, urllib.parse
UA = {'User-Agent': 'Nautilus-forraspróba/1.0 (nautilus.djp.hu; Verne-névadók ellenőrzése)'}
def get(u):
    for i in range(3):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode('utf-8'))
        except Exception as e:
            err = e; time.sleep(2 + 3 * i)
    return {'hiba': str(err)}
def wiki(lang, q):
    d = get(f'https://{lang}.wikipedia.org/w/api.php?action=query&format=json&generator=search&gsrlimit=3&prop=extracts|coordinates|info&inprop=url&exintro=1&explaintext=1&exlimit=max&redirects=1&gsrsearch=' + urllib.parse.quote(q))
    out = []
    for p in (d.get('query', {}).get('pages', {}).values() if isinstance(d, dict) else []):
        c = (p.get('coordinates') or [{}])[0]
        out.append({'lang': lang, 'title': p.get('title', ''), 'extract': (p.get('extract') or '')[:700], 'lat': c.get('lat'), 'lon': c.get('lon'), 'url': p.get('fullurl', '')})
    time.sleep(0.15)
    return out
def nomi(q):
    time.sleep(1.2)
    r = get('https://nominatim.openstreetmap.org/search?format=json&limit=3&addressdetails=0&q=' + urllib.parse.quote(q))
    return [{'name': x.get('display_name'), 'lat': x.get('lat'), 'lon': x.get('lon'), 'class': x.get('class'), 'type': x.get('type')} for x in r] if isinstance(r, list) else []
C = json.load(open('gyujto/nv_kerdesek.json'))
os.makedirs('proba', exist_ok=True)
with open('proba/nevadok.jsonl', 'w') as f:
    for c in C:
        langs = list(dict.fromkeys(c['lang'] + ['hu', 'en', 'fr', 'de']))
        w = []
        for l in langs:
            w += wiki(l, c['q'])
        n = nomi(', '.join(x for x in [c['q'], c['tel'], c['orsz']] if x)) if c['k7'] in ('kozterulet', 'emlekhely', 'oktatas', 'vendeglatas') else []
        f.write(json.dumps({'id': c['id'], 'wiki': w, 'osm': n}, ensure_ascii=False) + '\n'); f.flush()
    time.sleep(1.2)
    r = get('https://nominatim.openstreetmap.org/search?format=json&limit=50&countrycodes=hu&street=' + urllib.parse.quote('Verne Gyula utca'))
    f.write(json.dumps({'id': 'OSM-HU-VERNE-UTCA', 'osm': r}, ensure_ascii=False) + '\n')
open('proba/osszegzes.txt', 'w').write('kész: %d jelölt\n' % len(C))
# ujrainditas 1792758109
