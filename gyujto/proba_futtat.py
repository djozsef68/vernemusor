# Forráspróba: a megadott címek nyers letöltése (HTML), teljes mentés.
import json, os, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36', 'Accept-Language': 'hu,en'}
U = json.load(open('gyujto/proba_urls.json'))
os.makedirs('proba', exist_ok=True); ossz = []
for k, u in U.items():
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45)
        b = r.read().decode('utf-8', 'replace'); open(f'proba/{k}.html', 'w').write(b)
        ossz.append(f'{k} | {r.geturl()} | {len(b)}')
    except Exception as e:
        ossz.append(f'{k} | {u} | HIBA {e}')
open('proba/osszegzes.txt', 'w').write('\n'.join(ossz) + '\n')
