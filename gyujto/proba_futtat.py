# Forráspróba: Verne-névadók ellenőrzése – Wikipédia (keresés + bevezető + koordináta), OpenStreetMap (Overpass, Nominatim).
import json, os, time, urllib.request, urllib.parse
UA = {'User-Agent': 'Nautilus-forraspróba/1.0 (nautilus.djp.hu; Verne-névadók ellenőrzése)'}
def get(u, data=None):
    for i in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, data=data, headers=UA), timeout=90).read().decode('utf-8', 'replace')
        except Exception as e:
            err = e; time.sleep(4 + 6 * i)
    raise err
J = json.load(open('gyujto/proba_urls.json'))
os.makedirs('proba', exist_ok=True); ki = []
for azon, ny, q, *_ in J:
    r = {'azon': azon, 'q': q, 'talalat': []}
    for l in dict.fromkeys([ny, 'en', 'fr']):
        try:
            s = json.loads(get(f'https://{l}.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=3&srsearch=' + urllib.parse.quote(q)))
            cim = [x['title'] for x in s['query']['search']]
            if cim:
                d = json.loads(get(f'https://{l}.wikipedia.org/w/api.php?action=query&format=json&prop=extracts|coordinates|pageprops&exintro=1&explaintext=1&exchars=700&redirects=1&titles=' + urllib.parse.quote('|'.join(cim))))
                for p in d['query']['pages'].values():
                    c = p.get('coordinates', [{}])[0]
                    r['talalat'].append({'ny': l, 'cim': p.get('title'), 'kivonat': p.get('extract', '')[:700], 'lat': c.get('lat'), 'lon': c.get('lon'), 'wd': p.get('pageprops', {}).get('wikibase_item')})
        except Exception as e:
            r['talalat'].append({'ny': l, 'hiba': str(e)})
        time.sleep(0.3)
    ki.append(r)
json.dump(ki, open('proba/wiki.json', 'w'), ensure_ascii=False, indent=0)
# Overpass: Magyarország – Verne / Nautilus / Nemo / Phileas / Passepartout nevű helyek
oq = '[out:json][timeout:180];area["ISO3166-1"="HU"][admin_level=2]->.a;(nwr(area.a)["name"~"Verne|Nautilus|Nemo|Phileas|Passepartout|Fogg",i];);out center tags;'
try:
    open('proba/overpass_hu.json', 'w').write(get('https://overpass-api.de/api/interpreter', data=urllib.parse.urlencode({'data': oq}).encode()))
except Exception as e:
    open('proba/overpass_hu.json', 'w').write(json.dumps({'hiba': str(e)}))
# Nominatim: néhány utca
nom = {}
for q in ['Rue Jules Verne, Paris', 'Ulica Julesa Vernea, Pazin', 'Verne Gyula utca, Budapest', 'Verne Gyula utca, Miskolc', 'Verne Gyula utca, Ózd', 'Verne Gyula utca, Makó', 'Boulevard Jules Verne, Amiens', 'Rue Jules Verne, Nantes']:
    try:
        nom[q] = json.loads(get('https://nominatim.openstreetmap.org/search?format=jsonv2&limit=3&q=' + urllib.parse.quote(q)))
    except Exception as e:
        nom[q] = {'hiba': str(e)}
    time.sleep(1.2)
json.dump(nom, open('proba/nominatim.json', 'w'), ensure_ascii=False, indent=0)
open('proba/osszegzes.txt', 'w').write('wiki: %d jelölt\n' % len(ki))
