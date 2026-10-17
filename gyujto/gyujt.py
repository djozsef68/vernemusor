#!/usr/bin/env python3
# Verne-műsorfüzet: tévé, rádió, színház és mozi adatainak összegyűjtése egy JSON-fájlba.
# Csak a Python saját könyvtárait használja. Futtatás: python3 gyujto/gyujt.py data/musor.json
# Minden forrás külön próbálkozik – ha egy nem válaszol, a többi attól még bekerül,
# és a hiba a „forrasok” részben látszik.
import datetime as dt
import gzip
import html
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
from kulcsszavak import verne_e, cim_verne_e, egyszerusit  # noqa: E402

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36'
_suti = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
MOST = dt.datetime.now(dt.timezone.utc)


def letolt(url, nyelv='hu', ido=60):
    k = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': nyelv + ',en;q=0.6',
                                             'Accept': 'text/html,application/json,*/*'})
    for proba in range(2):
        try:
            with _suti.open(k, timeout=ido) as v:
                adat = v.read()
                if v.headers.get('Content-Encoding') == 'gzip' or adat[:2] == b'\x1f\x8b':
                    adat = gzip.decompress(adat)
                return adat
        except Exception:
            if proba:
                raise
            time.sleep(3)


def szoveg(h):
    h = re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>', ' ', h)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()


# ---------------------------------------------------------------- tévé és rádió
EPG = [('hu', 'HU1'), ('fr', 'FR1'), ('uk', 'UK1'), ('de', 'DE1'), ('it', 'IT1')]
RADIO = re.compile(r'(?i)\bradio\b|rádió|^MR\d|^BBC R(?:adio)?\b|^BBC R\d|^BBC 6 Music|^RTÉ (?:Radio|2FM|lyric)|France (?:Culture|Inter|Musique)|Deutschlandfunk|^Rai ?Radio')
KIHAGY = re.compile(r'(?i)brazzers|hustler|playboy|private|eroxxx|xxx|redlight|dorcel|blue hustler|\+1\b|\+24\b|\bsport|eurosport|bein|dazn|qvc|shop|news\b|\bnews|info\b|tg24|bloomberg|cnbc|cnn|euronews')
ATNEZVE = {}
# A forrás néhány rövid csatornaneve olvashatóbban
CSATORNANEV = {'20': '20 Mediaset', 'MR1-Kossuth': 'Kossuth Rádió', 'MR2-Petőfi': 'Petőfi Rádió',
               'MR3-Bartók': 'Bartók Rádió', 'MR4-Nemzetiségi': 'Nemzetiségi Rádió', 'MR6-Dankó': 'Dankó Rádió'}
EV = re.compile(r'(?<!\d)(18[89]\d|19\d\d|20[0-3]\d)(?!\d)')


def xmltv_ido(s):
    m = re.match(r'(\d{14})\s*([+-]\d{4})?', s or '')
    if not m:
        return None
    t = dt.datetime.strptime(m.group(1), '%Y%m%d%H%M%S')
    off = m.group(2) or '+0000'
    tz = dt.timezone(dt.timedelta(hours=int(off[:3]), minutes=int(off[0] + off[3:])))
    return t.replace(tzinfo=tz)


def epg_orszag(orszag, cimke):
    adat = letolt(f'https://epgshare01.online/epgshare01/epg_ripper_{cimke}.xml.gz', ido=300)
    nevek, ki, osszes = {}, [], 0
    for _, e in ET.iterparse(__import__('io').BytesIO(adat), events=('end',)):
        if e.tag == 'channel':
            nevek[e.get('id')] = (e.findtext('display-name') or e.get('id')).strip()
            e.clear()
        elif e.tag == 'programme':
            osszes += 1
            cim = (e.findtext('title') or '').strip()
            alcim = (e.findtext('sub-title') or '').strip()
            leiras = (e.findtext('desc') or '').strip()
            if verne_e(cim, alcim, leiras):
                csat = nevek.get(e.get('channel'), e.get('channel') or '')
                if not KIHAGY.search(csat) or RADIO.search(csat):
                    kezd, veg = xmltv_ido(e.get('start')), xmltv_ido(e.get('stop'))
                    if kezd and veg and veg > MOST - dt.timedelta(hours=1):
                        ev = (e.findtext('date') or '')[:4]
                        if not EV.fullmatch(ev or ''):
                            m = re.search(r'\((18[89]\d|19\d\d|20[0-3]\d)\)', cim)
                            ev = m.group(1) if m else ''
                        ki.append({
                            'tipus': 'radio' if RADIO.search(csat) else 'tv',
                            'orszag': orszag, 'csatorna': CSATORNANEV.get(csat, re.sub(r'\s+HD$', '', csat)), 'cim': cim,
                            'alcim': alcim if alcim and egyszerusit(alcim) != egyszerusit(cim) else '',
                            'ev': int(ev) if ev else None,
                            'kezd': kezd.isoformat(), 'perc': max(1, round((veg - kezd).total_seconds() / 60)),
                        })
            e.clear()
    ATNEZVE[cimke] = osszes
    return ki


# ---------------------------------------------------------------- Magyarország: port.hu (színház, mozi)
PORT = 'https://port.hu'
PORT_KERES = ['Jules Verne', 'Verne Gyula', '80 nap alatt a Föld körül', 'Nemo kapitány', 'Húszezer mérföld',
              'Sándor Mátyás', 'Sztrogoff', 'Rejtelmes sziget', 'Utazás a Föld középpontja felé', 'Grant kapitány',
              'Kétévi vakáció', 'Utazás a Holdba', 'Kárpáti kastély', 'Willy Fog', 'Ox doktor', 'Offenbach']
HONAP = {h: i + 1 for i, h in enumerate(['január', 'február', 'március', 'április', 'május', 'június', 'július',
                                          'augusztus', 'szeptember', 'október', 'november', 'december'])}


def port_jeloltek():
    linkek = []
    oldalak = [PORT + '/adatlap/szemely/jules-verne/person-18735'] + \
              [PORT + '/kereso?q=' + urllib.parse.quote_plus(k) for k in PORT_KERES]
    for u in oldalak:
        try:
            h = letolt(u).decode('utf-8', 'replace')
        except Exception:
            continue
        for l in re.findall(r'href="(/adatlap/(?:szindarab/[a-z-]+|film/mozi)/[^"#?]+)"', h):
            if l not in linkek:
                linkek.append(l)
        time.sleep(1)
    return linkek


def port_szinhaz(link, h):
    t = szoveg(h)
    m = re.search(r'Következő előadás (\d{4})\. (\w+) (\d{1,2})\. \(\w+\) (\d{1,2}:\d\d) (.+?) (\d{4}) ([^,]+),', t)
    if not m:
        return None
    cim = szoveg(re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S).group(1)) if re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S) else ''
    if not (cim_verne_e(cim) or re.search(r'(?i)jules verne|verne gyula', t)):
        return None
    tipus = re.search(r'/adatlap/szindarab/([a-z-]+)/', link).group(1)
    try:
        nap = dt.date(int(m.group(1)), HONAP[m.group(2).lower()], int(m.group(3)))
    except (KeyError, ValueError):
        return None
    mufaj = re.search(r'(opera|operett|musical|balett|táncjáték|bábjáték|gyerekműsor|zenés[^,]*)', t[:1500], re.I)
    return {'tipus': 'szinhaz', 'orszag': 'hu', 'cim': cim, 'hely': m.group(5).strip(),
            'varos': m.group(7).strip(), 'datum': nap.isoformat(), 'ido': m.group(4),
            'mufaj': (mufaj.group(1).lower() if mufaj else ('gyerekelőadás' if tipus == 'gyerekprogram' else '')),
            'link': PORT + link}


def port_mozi(link, h):
    cim_m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    cim = szoveg(cim_m.group(1)) if cim_m else ''
    t = szoveg(h)
    if not (cim_verne_e(cim) or re.search(r'(?i)jules verne|verne gyula', t)):
        return None
    varosok = dict(re.findall(r'<option value="(cityList-\d+)"[^>]*>([^<]+)</option>', h))
    helyek = {}
    for v, mozi in re.findall(r'<tr class="cinema-region-events-row" data-city_id="(cityList-\d+)"[^>]*>\s*<td[^>]*>\s*<a[^>]*>([^<]+)</a>', h):
        helyek.setdefault(varosok.get(v, ''), set()).add(html.unescape(mozi).strip())
    if not helyek:
        return None
    ev = re.search(r', \d+ perc, (\d{4})', t)
    return {'tipus': 'mozi', 'orszag': 'hu', 'cim': cim, 'ev': int(ev.group(1)) if ev else None,
            'helyek': [{'varos': v, 'mozik': sorted(m)} for v, m in sorted(helyek.items(), key=lambda x: (x[0] != 'Budapest', x[0]))],
            'link': PORT + link + '#cinema-events'}


def port_hu():
    sz, mo = [], []
    for l in port_jeloltek():
        try:
            h = letolt(PORT + l).decode('utf-8', 'replace')
        except Exception:
            continue
        r = port_mozi(l, h) if '/film/mozi/' in l else port_szinhaz(l, h)
        if r:
            (mo if r['tipus'] == 'mozi' else sz).append(r)
        time.sleep(1)
    return sz, mo


# ---------------------------------------------------------------- Magyarország: port.hu – a Verne-adatlap tévéadásai
# Jules Verne port.hu-adatlapja minden Verne-filmnél felsorolja a következő ~10 nap magyar tévéadásait
# (csatorna, nap, időpont) – a magyar csatornákra ez a legpontosabb forrás.
HO_ROVID = {'jan': 1, 'febr': 2, 'feb': 2, 'márc': 3, 'ápr': 4, 'máj': 5, 'jún': 6, 'júl': 7, 'aug': 8, 'szept': 9, 'szep': 9,
            'okt': 10, 'nov': 11, 'dec': 12}


def budapest_ido(d, hh, mm):
    # közép-európai idő nyári időszámítással (utolsó márciusi vasárnaptól utolsó októberi vasárnapig)
    def utolso_vasarnap(ev, ho):
        x = dt.date(ev, ho, 31)
        return x - dt.timedelta(days=(x.weekday() + 1) % 7)
    nyar = utolso_vasarnap(d.year, 3) <= d < utolso_vasarnap(d.year, 10)
    return dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=dt.timezone(dt.timedelta(hours=2 if nyar else 1)))


def csat_nev(c):
    return c.upper() if re.fullmatch(r'[a-z]\d', c) else c  # m1 → M1


def port_adasok(h):
    ki = []
    ma = MOST.astimezone(dt.timezone(dt.timedelta(hours=1))).date()
    for blokk in re.split(r'<li data-position-id=', h)[1:]:
        if 'event-place' not in blokk:
            continue
        c = re.search(r'<div class="release-info">\s*<a href="([^"]+)"[^>]*>([^<]+)</a>', blokk)
        if not c:
            continue
        cim = html.unescape(c.group(2)).strip()
        adat = re.search(r'\(([^()]*?),\s*(\d+) perc,\s*(\d{4})\)', blokk)
        perc = int(adat.group(2)) if adat else 0
        ev = int(adat.group(3)) if adat else None
        for csat_link, csat, napok in re.findall(r'<span class="event-place">\s*<a href="(/csatorna/[^"]+)"[^>]*>\s*<span class="event-date-link">\s*([^<:]+?):?\s*</span>.*?<ul class="event-date">(.*?)</ul>', blokk, re.S):
            for ho, nap, hh, mm in re.findall(r'\((\w+)\.\s*(\d{1,2})\.\)\s*(\d{1,2}):(\d{2})', napok):
                hon = HO_ROVID.get(ho.lower())
                if not hon:
                    continue
                ev_ = ma.year + (1 if hon < ma.month - 6 else 0)
                try:
                    kezd = budapest_ido(dt.date(ev_, hon, int(nap)), int(hh), int(mm))
                except ValueError:
                    continue
                if kezd + dt.timedelta(minutes=perc or 60) < MOST:
                    continue
                ki.append({'tipus': 'radio' if '/radio/' in csat_link else 'tv', 'orszag': 'hu',
                           'csatorna': csat_nev(html.unescape(csat).strip()), 'cim': cim, 'alcim': '', 'ev': ev,
                           'kezd': kezd.isoformat(), 'perc': perc or 60, 'link': PORT + c.group(1)})
    return ki


def port_tv():
    return port_adasok(letolt(PORT + '/adatlap/szemely/jules-verne/person-18735').decode('utf-8', 'replace'))


# ---------------------------------------------------------------- Anglia: ATG (színház)
ATG_KERES = ['verne', 'around the world in 80 days', '20,000 leagues', 'journey to the centre of the earth',
             'captain nemo', 'mysterious island', 'phileas fogg', 'from the earth to the moon', 'trip to the moon', 'offenbach']


def atg():
    ki, latott = [], set()
    for k in ATG_KERES:
        h = letolt('https://www.atgtickets.com/whats-on/?q=' + urllib.parse.quote_plus(k), 'en').decode('utf-8', 'replace')
        for blokk in h.split('MuiCardContent-root')[1:]:
            c = re.search(r'<h2[^>]*>([^<]+)</h2>', blokk)
            l = re.search(r'href="(/shows/[^"]+)"', blokk)
            if not c or not l or l.group(1) in latott:
                continue
            cim = html.unescape(c.group(1)).strip()
            if not cim_verne_e(cim):
                continue
            latott.add(l.group(1))
            p = [html.unescape(x).strip() for x in re.findall(r'<p class="MuiTypography-root[^"]*"[^>]*>([^<]+)</p>', blokk)]
            datum = next((x for x in p if re.search(r'\d{4}', x)), '')
            hely = next((x for x in p if x not in (datum,) and x != p[0]), '') if len(p) > 1 else ''
            ki.append({'tipus': 'szinhaz', 'orszag': 'uk', 'cim': cim, 'hely': hely, 'varos': '',
                       'idoszak': datum, 'mufaj': p[0].lower() if p else '',
                       'link': 'https://www.atgtickets.com' + l.group(1)})
        time.sleep(1)
    return ki


# ---------------------------------------------------------------- Franciaország: Offi (párizsi színház)
OFFI = ['/theatre/pieces-de-theatre.html', '/theatre/spectacles-musicaux.html', '/theatre/operas-ballets-danse.html',
        '/theatre/cirques-et-autres-spectacles.html', '/theatre/premieres.html', '/enfants/spectacles-enfants.html']


def offi():
    ki, latott = [], set()
    for o in OFFI:
        try:
            h = letolt('https://www.offi.fr' + o, 'fr').decode('utf-8', 'replace')
        except Exception:
            continue
        for l, t in re.findall(r'href="(/(?:theatre|enfants)/[a-z0-9-]+-\d+/[a-z0-9-]+-\d+\.html)"[^>]*>\s*([^<]{3,160}?)\s*<', h):
            t = html.unescape(t)
            if l in latott or not cim_verne_e(t):
                continue
            latott.add(l)
            resz = re.split(r' (?:à|au|aux|à la|à l\') (?=[A-ZÀ-Ýa-z])', t, maxsplit=1)
            cim, hely = resz[0], (resz[1] if len(resz) > 1 else '')
            ki.append({'tipus': 'szinhaz', 'orszag': 'fr', 'cim': cim.strip(), 'hely': hely.strip(), 'varos': 'Párizs',
                       'mufaj': '', 'link': 'https://www.offi.fr' + l})
        time.sleep(1)
    return ki


# ---------------------------------------------------------------- Franciaország: AlloCiné (mozi)
def allocine():
    ki, latott = [], set()
    for oldal in range(1, 25):
        h = letolt('https://www.allocine.fr/film/aucinema/' + (f'?page={oldal}' if oldal > 1 else ''), 'fr').decode('utf-8', 'replace')
        talalat = re.findall(r'<a class="meta-title-link" href="(/film/fichefilm_gen_cfilm=\d+\.html)"[^>]*>([^<]+)</a>', h)
        uj = [x for x in talalat if x[0] not in latott]
        if not uj:
            break
        for l, cim in uj:
            latott.add(l)
            cim = html.unescape(cim).strip()
            if cim_verne_e(cim):
                ki.append({'tipus': 'mozi', 'orszag': 'fr', 'cim': cim, 'ev': None, 'helyek': [],
                           'link': 'https://www.allocine.fr' + l})
        time.sleep(1)
    return ki


# ---------------------------------------------------------------- Olaszország: ComingSoon (mozi)
def comingsoon():
    ki = []
    h = letolt('https://www.comingsoon.it/cinema/filmalcinema/', 'it').decode('utf-8', 'replace')
    for blokk in re.split(r'<div class="cards cards-horiz-box', h)[1:]:
        m = re.search(r'href="(/film/[^"]+/scheda/)" title="([^"]+)"', blokk)
        if not m:
            continue
        cim = html.unescape(m.group(2)).strip()
        if not cim_verne_e(cim):
            continue
        sale = re.search(r'in <strong>(\d+)</strong> sale', blokk)
        ev = re.search(r'<b>Anno:</b> <span>(\d{4})', blokk)
        ki.append({'tipus': 'mozi', 'orszag': 'it', 'cim': cim, 'ev': int(ev.group(1)) if ev else None, 'helyek': [],
                   'mozik_szama': int(sale.group(1)) if sale else None, 'link': 'https://www.comingsoon.it' + m.group(1)})
    return ki


# ---------------------------------------------------------------- Ticketmaster (csak ha van kulcs)
def ticketmaster(kulcs):
    ki, latott, jo, hiba, lat = [], set(), 0, '', 0
    for orszag, kod in [('uk', 'GB'), ('de', 'DE'), ('fr', 'FR'), ('it', 'IT'), ('hu', 'HU')]:
        for k in ['Jules Verne', 'Around the World in 80 Days', 'Nemo', 'Strogoff', 'Phileas Fogg', 'Offenbach', 'Voyage dans la lune', 'Docteur Ox']:
            u = ('https://app.ticketmaster.com/discovery/v2/events.json?size=50&countryCode=' + kod +
                 '&keyword=' + urllib.parse.quote(k) + '&apikey=' + kulcs)
            try:
                d = json.loads(letolt(u, 'en'))
                jo += 1
            except Exception as e:
                hiba = str(e)[:120]
                continue
            lat += len(d.get('_embedded', {}).get('events', []))
            for e in d.get('_embedded', {}).get('events', []):
                if e.get('id') in latott or not cim_verne_e(e.get('name', '')):
                    continue
                latott.add(e['id'])
                v = (e.get('_embedded', {}).get('venues') or [{}])[0]
                st = e.get('dates', {}).get('start', {})
                besorolas = ((e.get('classifications') or [{}])[0].get('segment') or {}).get('name', '')
                ki.append({'tipus': 'mozi' if besorolas == 'Film' else 'szinhaz', 'orszag': orszag, 'cim': e['name'],
                           'hely': v.get('name', ''), 'varos': (v.get('city') or {}).get('name', ''),
                           'datum': st.get('localDate', ''), 'ido': (st.get('localTime') or '')[:5], 'mufaj': '',
                           'helyek': [], 'link': e.get('url', '')})
            time.sleep(0.3)
    if not jo:
        raise RuntimeError('a Ticketmaster egyik kérésre sem válaszolt: ' + hiba)
    try:  # ellenőrzés: egy biztosan létező keresés – ha ez is üres, a keresés módjával van baj, nem a műsorral
        d = json.loads(letolt('https://app.ticketmaster.com/discovery/v2/events.json?size=1&countryCode=GB&keyword=theatre&apikey=' + kulcs, 'en'))
        ATNEZVE['ticketmaster-proba'] = d.get('page', {}).get('totalElements', 0)
    except Exception:
        ATNEZVE['ticketmaster-proba'] = -1
    ATNEZVE['ticketmaster'] = lat
    return ki


# ---------------------------------------------------------------- összerakás
def main():
    ki_fajl = sys.argv[1] if len(sys.argv) > 1 else 'data/musor.json'
    eredmeny = {'frissitve': MOST.replace(microsecond=0).isoformat(), 'tv': [], 'radio': [], 'szinhaz': [], 'mozi': [],
                'forrasok': {}}

    def fut(nev, f):
        t0 = time.time()
        try:
            r = f()
            eredmeny['forrasok'][nev] = {'ok': True, 'db': sum(len(x) for x in r) if isinstance(r, tuple) else len(r),
                                         'mp': round(time.time() - t0)}
            if nev == 'ticketmaster' and 'ticketmaster-proba' in ATNEZVE:
                eredmeny['forrasok'][nev]['proba'] = ATNEZVE['ticketmaster-proba']
            if nev.split()[-1] in ATNEZVE:
                eredmeny['forrasok'][nev]['atnezve'] = ATNEZVE[nev.split()[-1]]
            return r
        except Exception as e:  # a forrás hibája nem állítja meg a többit
            eredmeny['forrasok'][nev] = {'ok': False, 'hiba': str(e)[:200], 'mp': round(time.time() - t0)}
            return ([], []) if nev == 'port.hu' else []

    for orszag, cimke in EPG:
        for m in fut('epgshare01 ' + cimke, lambda o=orszag, c=cimke: epg_orszag(o, c)):
            eredmeny[m.pop('tipus')].append(m)
    for m in fut('port.hu tévé', port_tv):
        eredmeny[m.pop('tipus')].append(m)
    sz, mo = fut('port.hu', port_hu)
    eredmeny['szinhaz'] += sz
    eredmeny['mozi'] += mo
    eredmeny['szinhaz'] += fut('atgtickets.com', atg)
    eredmeny['szinhaz'] += fut('offi.fr', offi)
    eredmeny['mozi'] += fut('allocine.fr', allocine)
    eredmeny['mozi'] += fut('comingsoon.it', comingsoon)
    if os.environ.get('TICKETMASTER_KULCS'):
        for m in fut('ticketmaster', lambda: ticketmaster(os.environ['TICKETMASTER_KULCS'])):
            eredmeny[m['tipus']].append(m)

    for k in ('tv', 'radio'):  # ismétlődések (ugyanaz a csatorna, ugyanakkor) és rendezés
        egyedi = {}
        for m in eredmeny[k]:
            cs = re.sub(r'[^a-z0-9]', '', m['csatorna'].lower())
            cs = re.sub(r'(hd|uhd|4k)$', '', cs)
            egyedi.setdefault((cs, dt.datetime.fromisoformat(m['kezd']).astimezone(dt.timezone.utc)), m)
        lista = sorted(egyedi.values(), key=lambda m: (dt.datetime.fromisoformat(m['kezd']).astimezone(dt.timezone.utc), m['orszag'], m['csatorna']))
        # Ugyanaz a műsor ugyanazon a csatornán 45 percen belül kétszer: a forrás két adatszolgáltatója
        # eltérő időt ad (pl. 07:26 és 07:41). A korábbit tartjuk meg – így biztosan nem marad le róla senki.
        tartott = []
        for m in lista:
            t = dt.datetime.fromisoformat(m['kezd'])
            kulcs = (re.sub(r'[^a-z0-9]', '', m['csatorna'].lower()), egyszerusit(m['cim']))
            if any(x[0] == kulcs and abs((t - x[1]).total_seconds()) < 45 * 60 for x in tartott):
                continue
            tartott.append((kulcs, t, m))
        eredmeny[k] = [x[2] for x in tartott]
    for m in eredmeny['szinhaz'] + eredmeny['mozi']:
        m.pop('tipus', None)
    eredmeny['szinhaz'].sort(key=lambda m: (m.get('datum') or '9999', m['orszag'], m['cim']))
    eredmeny['mozi'].sort(key=lambda m: (m['orszag'] != 'hu', m['orszag'], m['cim']))

    os.makedirs(os.path.dirname(ki_fajl) or '.', exist_ok=True)
    with open(ki_fajl, 'w', encoding='utf-8') as f:
        json.dump(eredmeny, f, ensure_ascii=False, indent=1)
    for k in ('tv', 'radio', 'szinhaz', 'mozi'):
        print(f'{k}: {len(eredmeny[k])}')
    for n, f in eredmeny['forrasok'].items():
        print(n, f)


if __name__ == '__main__':
    main()
