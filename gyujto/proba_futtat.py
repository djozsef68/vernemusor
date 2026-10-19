# Próba: képregény-források szöveges kivonata + online olvasható példányok keresése
import re, html, os, json, urllib.request, urllib.parse
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36', 'Accept-Language': 'en,fr,es,pt,hu'}
def get(u, n=60):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=n).read()
def txt(b):
    h = b.decode('utf-8', 'replace')
    h = re.sub(r'(?is)<(script|style|nav|footer).*?</\1>', ' ', h)
    t = html.unescape(re.sub(r'<[^>]+>', '\n', h))
    return '\n'.join(s.strip() for s in t.splitlines() if s.strip())
URLS = {
 'openedition': 'https://journals.openedition.org/carnets/9034',
 'valentin': 'https://misinolvidablestebeos.blogspot.com/2025/07/veinte-mil-leguas-de-viaje-submarino.html',
 'powerblog': 'http://powerrecord.blogspot.com/2008/06/20000-leagues-under-sea.html',
 'gcd_acclaim': 'https://www.comics.org/issue/352040/',
 'gcd_sup81': 'https://www.comics.org/issue/10355/?issue_detail=2',
 'gcd_3d': 'https://www.comics.org/series/46127/overview/',
 'gcd_power': 'https://www.comics.org/series/26697/',
 'sevenseas': 'https://sevenseasentertainment.com/series/captain-nemo/',
 'mobilis': 'https://tkopresents.com/products/mobilis',
 'krapp': 'https://www.thilo-krapp.com/en/20000-leagues-under-the-sea-graphic-novel/',
 'autentica': 'https://www.autenticaeditora.com.br/pnld/manual/798',
 'paico': 'https://en.wikipedia.org/wiki/PAICO_Classics',
 'kiefer': 'https://en.wikipedia.org/wiki/Henry_C._Kiefer',
 'adapt': 'https://en.wikipedia.org/wiki/Adaptations_of_Twenty_Thousand_Leagues_Under_the_Seas',
}
ki = []
for k, u in URLS.items():
    try:
        t = txt(get(u))
        # csak a releváns sorok környezete
        if len(t) > 7000:
            sor = t.splitlines(); keep = set()
            for i, s in enumerate(sor):
                if re.search(r'(?i)leagues|lieues|leguas|léguas|nemo|verne|comic|bande|banda|quadrinho|historieta|tebeo|pages?|páginas|isbn|online|download|descarg|leer|lire|read', s):
                    keep.update(range(max(0, i-1), min(len(sor), i+2)))
            t = '\n'.join(sor[i] for i in sorted(keep))
        ki.append(f'===== {k} {u}\n{t[:9000]}')
    except Exception as e:
        ki.append(f'===== {k} HIBA {e}')
# Verniana PDF – csak a szöveg (pdftotext ha van)
try:
    open('/tmp/v.pdf', 'wb').write(get('https://www.verniana.org/volumes/04/A4/WilliamJones.pdf', 90))
    os.system('pdftotext -layout /tmp/v.pdf /tmp/v.txt 2>/dev/null')
    t = open('/tmp/v.txt', errors='replace').read() if os.path.exists('/tmp/v.txt') else ''
    sor = t.splitlines(); keep = set()
    for i, s in enumerate(sor):
        if re.search(r'(?i)leagues|lieues|nemo|comic|bande|classics|gianni|kiefer', s):
            keep.update(range(max(0, i-2), min(len(sor), i+3)))
    ki.append('===== verniana PDF\n' + '\n'.join(sor[i] for i in sorted(keep))[:15000])
except Exception as e:
    ki.append(f'===== verniana HIBA {e}')
# archive.org: képregény-példányok
for q in ['title:("20,000 Leagues" OR "20000 Leagues" OR "Twenty Thousand Leagues" OR "20.000 leguas" OR "vingt mille lieues" OR "20 000 lieues") AND (comic OR comics OR "Classics Illustrated" OR "Four Color" OR "bande dessinee" OR historieta OR tebeo)',
          'subject:(comics) AND (verne OR nemo) AND (leagues OR lieues OR leguas)']:
    try:
        u = 'https://archive.org/advancedsearch.php?' + urllib.parse.urlencode({'q': q, 'fl[]': ['identifier', 'title', 'date', 'mediatype'], 'rows': 80, 'output': 'json'}, doseq=True)
        d = json.loads(get(u))
        ki.append('===== archive.org ' + q + '\n' + '\n'.join(f"{x.get('identifier')} | {x.get('title')} | {x.get('date','')} | {x.get('mediatype')}" for x in d['response']['docs']))
    except Exception as e:
        ki.append(f'===== archive HIBA {e}')
# comicbookplus és Digital Comic Museum keresés
for k, u in {'cbplus': 'https://comicbookplus.com/?cbplus=search&q=20000+leagues', 'cbplus2': 'https://comicbookplus.com/?cbplus=search&q=nemo',
             'dcm': 'https://digitalcomicmuseum.com/index.php?ACT=search&terms=leagues'}.items():
    try:
        t = txt(get(u)); sor = [s for s in t.splitlines() if re.search(r'(?i)league|nemo|verne', s)]
        ki.append(f'===== {k}\n' + '\n'.join(sor[:60]))
    except Exception as e:
        ki.append(f'===== {k} HIBA {e}')
os.makedirs('proba', exist_ok=True)
open('proba/osszegzes.txt', 'w').write('\n\n'.join(ki) + '\n')
print(len('\n\n'.join(ki)))
