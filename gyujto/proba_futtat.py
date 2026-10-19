import re, html, os, json, urllib.request, concurrent.futures as cf
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36', 'Accept-Language': 'en,fr,es,pt,de'}
U = json.load(open('gyujto/proba_urls.json'))
KW = r'(?i)átdolg|fordít|kiadó|kiadás|oldal|Nemo kapit|Húszezer|20 ?000|leagues|lieues|leguas|léguas|meilen|nemo|nautilus|verne|海底|해저|premi|création|estreno|estreia|20\.?000|20 000|season|saison|temporada|dates?|date|year|\b(19|20)\d\d\b'
def one(k, u):
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45).read()
        if u.endswith('.pdf'):
            open('/tmp/x.pdf','wb').write(b); os.system('pdftotext /tmp/x.pdf /tmp/x.txt 2>/dev/null'); t=open('/tmp/x.txt',errors='replace').read()
        else:
            h = re.sub(r'(?is)<(script|style|nav|footer|header).*?</\1>', ' ', b.decode('utf-8','replace'))
            t = html.unescape(re.sub(r'<[^>]+>', '\n', h))
        sor = [s.strip() for s in t.splitlines() if s.strip()]
        keep = [s for s in sor if re.search(KW, s) and len(s) < 600]
        return f'===== {k} | {u}\n' + '\n'.join(keep[:60])[:3500]
    except Exception as e:
        return f'===== {k} | {u}\nHIBA {e}'
with cf.ThreadPoolExecutor(8) as ex:
    res = list(ex.map(lambda kv: one(*kv), U.items()))
os.makedirs('proba', exist_ok=True); open('proba/osszegzes.txt','w').write('\n\n'.join(res)+'\n')
