# Próba: OSA Diafilm-archívum – két Nemo kapitány tétel (szöveges kivonat)
import re, html, os, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/126 Safari/537.36', 'Accept-Language': 'hu,en'}
ki = []
for fs in ('2324', '3212'):
    for u in (f'http://diafilm.osaarchivum.org/public/?fs={fs}', f'http://diafilm.osaarchivum.org/public/index.php?fs={fs}&lang=hu'):
        try:
            h = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode('utf-8', 'replace')
        except Exception as e:
            ki.append(f'HIBA {u}: {e}'); continue
        h = re.sub(r'(?is)<(script|style).*?</\1>', ' ', h)
        t = html.unescape(re.sub(r'<[^>]+>', '\n', h))
        t = '\n'.join(s.strip() for s in t.splitlines() if s.strip())
        imgs = re.findall(r'(?i)src="([^"]+\.(?:jpg|png))"', h)[:5]
        ki.append(f'===== {u}\n{t[:6000]}\n-- képek: {imgs}')
        break
os.makedirs('proba', exist_ok=True)
open('proba/osszegzes.txt', 'w').write('\n\n'.join(ki) + '\n')
print('\n\n'.join(ki)[:4000])
