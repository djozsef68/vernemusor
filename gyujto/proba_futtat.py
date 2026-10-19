import re, html, os, json, urllib.request, urllib.parse
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36', 'Accept-Language': 'en,fr,es,it'}
def get(u, n=60): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=n).read()
def txt(b):
    h = re.sub(r'(?is)<(script|style).*?</\1>', ' ', b.decode('utf-8', 'replace'))
    t = html.unescape(re.sub(r'<[^>]+>', '\n', h)); return '\n'.join(s.strip() for s in t.splitlines() if s.strip())
ki = []
for i in ['20000leaguesunde0000unse_j5h9','20000leguasdevia0000bind','20000leaguesunde0000gran','20000leaguesunde00bowe','graphicrevolve200000bowe','20240819_20240819_1818','lccn_73075466','julesvernes200000000bowe_q7x7','julesvernes200000000bowe']:
    try:
        m = json.loads(get(f'https://archive.org/metadata/{i}'))['metadata']
        ki.append(f"### {i}\n" + '\n'.join(f"{k}: {str(m.get(k))[:300]}" for k in ['title','creator','publisher','date','description','subject','collection','access-restricted-item','isbn','language','imagecount']))
    except Exception as e: ki.append(f'### {i} HIBA {e}')
for k,u in {'profH1':'http://professorhswaybackmachine.blogspot.com/2013/08/jules-verne.html','profH16':'http://professorhswaybackmachine.blogspot.com/2014/06/jules-verne-part-16.html',
            'inducks':'https://inducks.org/story.php?c=I+TL+3355-1P','crotoy':'https://www.bdphile.fr/album/bd/178324-voyage-extraordinaire-au-crotoy',
            'andrzejewski':'https://pl.wikipedia.org/wiki/Waldemar_Andrzejewski','bento':'https://biblobd.blogspot.com/2018/05/fernando-bento-ensaio-de.html',
            'rochette':'https://en.wikipedia.org/wiki/Jean-Marc_Rochette','spiegle':'https://en.wikipedia.org/wiki/Dan_Spiegle'}.items():
    try:
        t = txt(get(u)); sor=t.splitlines(); keep=set()
        for j,s in enumerate(sor):
            if re.search(r'(?i)leagues|lieues|leguas|léguas|leghe|nemo|verne|nautilus|mila', s): keep.update(range(max(0,j-2),min(len(sor),j+3)))
        ki.append(f'===== {k}\n' + '\n'.join(sor[j] for j in sorted(keep))[:6000])
    except Exception as e: ki.append(f'===== {k} HIBA {e}')
os.makedirs('proba', exist_ok=True); open('proba/osszegzes.txt','w').write('\n\n'.join(ki)+'\n')
