# Próba: az ARTE kínálatából minden Verne-vonatkozású, most nézhető műsor (6 nyelven)
import re, html, json, time, urllib.request, urllib.parse, os
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'}
def letolt(u, ny):
    r = urllib.request.Request(u, headers=dict(UA, **{'Accept-Language': ny}))
    return urllib.request.urlopen(r, timeout=40).read().decode('utf-8', 'replace')
Q = {
 'fr': ['jules verne', 'vingt mille lieues sous les mers', 'tour du monde en 80 jours', 'capitaine nemo', 'voyage au centre de la terre', "l'île mystérieuse", 'michel strogoff', 'de la terre à la lune', 'nautilus sous-marin', 'phileas fogg'],
 'de': ['jules verne', '20000 meilen unter dem meer', 'in 80 tagen um die welt', 'kapitän nemo', 'reise zum mittelpunkt der erde'],
 'en': ['jules verne', 'twenty thousand leagues', 'around the world in 80 days'],
 'es': ['julio verne', 'la vuelta al mundo en 80 días'],
 'it': ['jules verne', 'giro del mondo in 80 giorni'],
 'pl': ['juliusz verne', 'w 80 dni dookoła świata'],
}
talalat = {}
for ny, qs in Q.items():
    for q in qs:
        try:
            h = letolt(f'https://www.arte.tv/{ny}/search/?q=' + urllib.parse.quote(q), ny)
        except Exception as e:
            print('HIBA', ny, q, e); continue
        h = h.replace('\\"', '"').replace('\\u0026', '&')
        for blokk in h.split('{"deeplink":"arte://program/')[1:]:
            pid = blokk.split('"', 1)[0]
            def mezo(n):
                m = re.search(r'"' + n + r'":"((?:[^"\\]|\\.)*)"', blokk)
                return html.unescape(m.group(1)) if m else ''
            veg = re.search(r'"availability":\{"end":"([^"]+)"', blokk)
            kezd = re.search(r'"availability":\{[^}]*"start":"([^"]+)"', blokk)
            dur = re.search(r'"duration":(\d+)', blokk)
            u = re.search(r'"url":"(/' + ny + r'/videos/[^"]*)"', blokk)
            cim, alcim, leiras = mezo('title'), mezo('subtitle'), mezo('shortDescription')
            k = pid + '|' + ny
            if k in talalat: talalat[k]['q'].add(q); continue
            talalat[k] = dict(ny=ny, pid=pid, cim=cim, alcim=alcim, leiras=leiras[:400], veg=veg.group(1)[:10] if veg else '',
                              kezd=kezd.group(1)[:10] if kezd else '', perc=round(int(dur.group(1))/60) if dur else '',
                              url='https://www.arte.tv' + (u.group(1) if u else f'/{ny}/videos/{pid}/'), q={q},
                              verne=bool(re.search(r'(?i)verne|nemo|fogg|nautilus', cim + alcim + leiras)))
        time.sleep(1)
os.makedirs('proba', exist_ok=True)
sorok = []
for v in sorted(talalat.values(), key=lambda x: (not x['verne'], x['pid'], x['ny'])):
    sorok.append(f"{'V' if v['verne'] else '-'} [{v['ny']}] {v['pid']} | {v['cim']} | {v['alcim']} | {v['perc']} perc | {v['kezd']} → {v['veg']} | {v['url']}\n    {v['leiras'][:300]}\n    (keresés: {', '.join(sorted(v['q']))})")
open('proba/osszegzes.txt', 'w').write(f"ARTE-próba – {len(talalat)} találat, ebből Verne-gyanús: {sum(v['verne'] for v in talalat.values())}\n\n" + '\n'.join(sorok) + '\n')
print(open('proba/osszegzes.txt').read()[:3000])
