import re, html, os, json, urllib.request, urllib.parse
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36', 'Accept-Language': 'en,fr,es,it'}
def get(u, n=60): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=n).read()
def txt(b):
    h = re.sub(r'(?is)<(script|style).*?</\1>', ' ', b.decode('utf-8', 'replace'))
    t = html.unescape(re.sub(r'<[^>]+>', '\n', h)); return '\n'.join(s.strip() for s in t.splitlines() if s.strip())
ki = []
for k,u in {'mickey55':'https://bdoubliees.com/mickey/annees/1955.htm','delafuente':'https://www.bedetheque.com/serie-34527-BD-20-000-lieues-sous-les-mers-De-La-Fuente.html',
 'bruno':'https://www.bedetheque.com/serie-1317-BD-Nemo-Bruno.html','gc34':'https://www.bedetheque.com/BD-Grands-Classiques-de-la-litterature-en-bande-dessinee-Tome-34-20-000-Lieues-sous-les-Mers-329848.html',
 'lillo':'https://www.tebeosfera.com/autores/h_lillo_lutteroth.html','tebverne':'https://www.tebeosfera.com/autores/verne_jules.html','largo':'https://largodoscorreios.wordpress.com/2018/04/03/20-000-leguas-submarinas/',
 'msu':'https://comics.lib.msu.edu/rri/nrri/naut.htm','andrz':'https://pl.wikipedia.org/wiki/Waldemar_Andrzejewski','retour':'https://www.altaplana.be/en/albums/le-retour-du-capitaine-nemo',
 'gcd_dh':'https://www.comics.org/issue/52248/','profH1':'http://professorhswaybackmachine.blogspot.com/2013/08/jules-verne.html'}.items():
    try:
        b=get(u); t = txt(b); sor=t.splitlines(); keep=set()
        for j,s in enumerate(sor):
            if re.search(r'(?i)leagues|lieues|leguas|léguas|nemo|nautilus|mila|verne|kapitan', s): keep.update(range(max(0,j-3),min(len(sor),j+4)))
        links=[x for x in re.findall(r'href="([^"]+)"', b.decode('utf-8','replace')) if re.search(r'(?i)gilead|zvi|leagues|lieues|nemo|verne', x)][:30]
        ki.append(f'===== {k}\n' + '\n'.join(sor[j] for j in sorted(keep))[:7000] + '\n-- linkek: ' + ' '.join(links))
    except Exception as e: ki.append(f'===== {k} HIBA {e}')
os.makedirs('proba', exist_ok=True); open('proba/osszegzes.txt','w').write('\n\n'.join(ki)+'\n')
