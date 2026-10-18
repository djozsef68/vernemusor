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
EPG = [('hu', 'HU1'), ('fr', 'FR1'), ('uk', 'UK1'), ('de', 'DE1'), ('it', 'IT1'), ('es', 'ES1'), ('pt', 'PT1'), ('pl', 'PL1'),
       ('ch', 'CH1'), ('be', 'BE2'), ('us', 'US2'),
       ('ru', 'https://iptvx.one/epg/epg_noarch.xml.gz')]  # orosz nyelvű adók: az iptvx.one gyűjtése (az iptv-org egyik forrása)
RADIO = re.compile(r'(?i)\bradio\b|rádió|радио|^RNE\b|^RTP Antena|Jedynka|Dwójka|Trójka|^MR\d|^BBC R(?:adio)?\b|^BBC R\d|^BBC 6 Music|^RTÉ (?:Radio|2FM|lyric)|France (?:Culture|Inter|Musique)|Deutschlandfunk|^Rai ?Radio')
KIHAGY = re.compile(r'(?i)brazzers|hustler|playboy|private|eroxxx|xxx|redlight|dorcel|blue hustler|\(\+\d+\)|\+\d+\b|\bsport|eurosport|bein|dazn|qvc|shop|news\b|\bnews|info\b|tg24|bloomberg|cnbc|cnn|euronews')
ATNEZVE = {}
# Osztrák, svájci, belga adók felismerése a nevük alapján (a német és a francia fájlban is vannak ilyenek;
# a svájci és a belga fájlból csak ezek kellenek, a többi csatornájuk máshonnan is megvan)
ADO_ORSZAG = [
    ('at', re.compile(r'(?i)^(?:ORF|ATV|PULS ?(?:4|24|8)|Servus ?TV|oe24|ServusTV)')),
    ('ch', re.compile(r'(?i)^(?:SRF|RTS|RSI|[3-6]\+|TV ?2[45]\b|S1\b|Blue ?Zoom|Tele ?Z[üu]ri|Tele ?B[äa]rn|CH ?Media|Teleclub|La T[ée]l[ée]\b|L[ée]man Bleu|Canal 9)')),
    ('be', re.compile(r'(?i)^(?:La ?Une|Tipik|La ?Trois|RTL[- ]?TVI|Club ?RTL|Plug ?RTL|AB ?3|ABXPLORE|Be ?1\b|BE ?1\b|Be ?Cin[ée]|Be ?S[ée]ries|LN24|BX1|Ketnet|VRT|[ée][ée]n\b|Canvas|VTM|Play ?[4-7]|Arte Belgique|Canal ?Z|Vier\b|Vijf\b|ZES\b)')),
]


def ado_orszag(csat, alap):
    for o, minta in ADO_ORSZAG:
        if minta.search(csat):
            return o
    return None if alap in ('ch', 'be') else alap
# Az orosz gyűjtés (iptvx.one) több ezer, sokszor kétes IPTV-csatornát is tartalmaz – csak az ismert orosz adók számítanak.
RU_ADOK = re.compile(r'(?i)^(?:Первый канал|Россия[ -]?(?:1|К|Культура)|Культура|НТВ|Пятый канал|5 канал|СТС|ТНТ|Домашний|Карусель|Мульт|'
                     r'Дом кино|Кинопоказ|Мосфильм|Золотая коллекция|Советское кино|Звезда|ТВ Центр|ТВЦ|РЕН ТВ|Пятница|ТВ-3|Ностальгия|'
                     r'Время|Радио России|Маяк|Вести ФМ|Радио Культура|Радио Звезда)(?:\s|$|\(|HD)')
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
    adat = letolt(cimke if cimke.startswith('http') else f'https://epgshare01.online/epgshare01/epg_ripper_{cimke}.xml.gz', 'ru' if orszag == 'ru' else 'hu', ido=300)
    nevek, ki, osszes, radio = {}, [], 0, {}
    for _, e in ET.iterparse(__import__('io').BytesIO(adat), events=('end',)):
        if e.tag == 'channel':
            nevek[e.get('id')] = (e.findtext('display-name') or e.get('id')).strip()
            e.clear()
        elif e.tag == 'programme':
            osszes += 1
            rc = nevek.get(e.get('channel'), '')
            if rc and RADIO.search(rc):
                radio[rc] = radio.get(rc, 0) + 1
            cim = (e.findtext('title') or '').strip()
            alcim = (e.findtext('sub-title') or '').strip()
            leiras = (e.findtext('desc') or '').strip()
            if verne_e(cim, alcim, leiras):
                csat = nevek.get(e.get('channel'), e.get('channel') or '')
                hol = ado_orszag(csat, orszag)
                if hol and (not KIHAGY.search(csat) or RADIO.search(csat)) and (orszag != 'ru' or RU_ADOK.search(csat)):
                    kezd, veg = xmltv_ido(e.get('start')), xmltv_ido(e.get('stop'))
                    if kezd and veg and veg > MOST - dt.timedelta(hours=1):
                        ev = (e.findtext('date') or '')[:4]
                        if not EV.fullmatch(ev or ''):
                            m = re.search(r'\((18[89]\d|19\d\d|20[0-3]\d)\)', cim)
                            ev = m.group(1) if m else ''
                        ki.append({
                            'tipus': 'radio' if RADIO.search(csat) and not re.search(r'(?i)\bTV\b|Vision|Telewizja', csat) else 'tv',
                            'orszag': hol, 'csatorna': CSATORNANEV.get(csat, re.sub(r'\s+HD$', '', csat)), 'cim': cim,
                            'alcim': alcim if alcim and egyszerusit(alcim) != egyszerusit(cim) else '',
                            'ev': int(ev) if ev else None,
                            'kezd': kezd.isoformat(), 'perc': max(1, round((veg - kezd).total_seconds() / 60)),
                        })
            e.clear()
    ATNEZVE['RU' if cimke.startswith('http') else cimke] = osszes
    ATNEZVE['radio-' + ('RU' if cimke.startswith('http') else cimke)] = radio
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


PORT_TV_KERES = ['verne', 'jules verne', 'verne gyula', 'nemo kapitány', '80 nap alatt', 'sándor mátyás', 'rejtelmes sziget',
                 'föld középpontja', 'grant kapitány', 'sztrogoff', 'kétévi vakáció', 'dunai hajós', 'utazás a holdba']


def port_tvkereses():
    """A port.hu tévéműsor-keresője: a Verne-ről szóló dokumentumfilmeket és a leírásban említett adásokat is megtalálja."""
    ki, cikk, ver = [], 0, 0
    for q in PORT_TV_KERES:
        try:
            h = letolt(PORT + '/kereso?q=' + urllib.parse.quote_plus(q) + '&type=tvevent').decode('utf-8', 'replace')
        except Exception:
            continue
        for a in re.findall(r'<article data-category="[^"]*">(.*?)</article>', h, re.S):
            cikk += 1
            c = re.search(r'<a class="title" href="([^"]+)"[^>]*>\s*([^<]+?)\s*</a>', a)
            e = re.search(r'<p class="events">(.*?)</p>', a, re.S)
            if not c or not e:
                continue
            cim = html.unescape(c.group(2)).strip()
            leir = szoveg(re.search(r'<p class="description">(.*?)</p>', a, re.S).group(1)) if '<p class="description">' in a else ''
            if not verne_e(cim, leir):
                continue
            ver += 1
            osszeg = szoveg(re.search(r'<label class="summary">(.*?)(?:<img|</label>)', a, re.S).group(1)) if '<label class="summary">' in a else ''
            ev = re.search(r'(18[89]\d|19\d\d|20[0-3]\d)\s*$', osszeg)
            perc = re.search(r'(\d+) perc', osszeg)
            sorok = [szoveg(x) for x in re.split(r'<br\s*/?>', e.group(1)) if szoveg(x)]
            csat = ''
            for sor in sorok:
                m = re.match(r'(?:(.+?) - )?(\d{4})\. (\w+)\. (\d{1,2})\. (\d{1,2}):(\d{2})$', sor)
                if not m:
                    continue
                csat = m.group(1) or csat
                hon = HO_ROVID.get(m.group(3).lower())
                if not hon or not csat:
                    continue
                try:
                    kezd = budapest_ido(dt.date(int(m.group(2)), hon, int(m.group(4))), int(m.group(5)), int(m.group(6)))
                except ValueError:
                    continue
                if kezd + dt.timedelta(minutes=int(perc.group(1)) if perc else 60) < MOST:
                    continue
                ki.append({'tipus': 'radio' if re.search(r'(?i)rádió|radio', csat) else 'tv', 'orszag': 'hu',
                           'csatorna': csat_nev(html.unescape(csat).strip()), 'cim': cim, 'alcim': '',
                           'ev': int(ev.group(1)) if ev else None, 'kezd': kezd.isoformat(),
                           'perc': int(perc.group(1)) if perc else 0, 'link': PORT + c.group(1)})
        time.sleep(1)
    ATNEZVE['tévékereső'] = cikk
    ATNEZVE['tévékereső-verne'] = ver
    return ki


def port_tv():
    return port_adasok(letolt(PORT + '/adatlap/szemely/jules-verne/person-18735').decode('utf-8', 'replace'))


# ---------------------------------------------------------------- Rádiók saját műsorlapjai (FR, DE, AT)
def napok(db=7):
    ma = MOST.astimezone(dt.timezone(dt.timedelta(hours=1))).date()
    return [ma + dt.timedelta(days=i) for i in range(db)]


def radiofrance(adoazon, nev):
    ki, lat = [], 0
    for nap in napok():
        try:
            h = letolt(f'https://www.radiofrance.fr/{adoazon}/grille-programmes?date={nap:%d-%m-%Y}', 'fr').decode('utf-8', 'replace')
        except Exception:
            continue
        elemek = []
        for b in h.split('timeline-item')[1:]:
            t = re.search(r'starttimeunix="(\d+)"', b)
            c = re.search(r'aria-label="([^"]+)"', b)
            if not t or not c:
                continue
            al = re.search(r'class="typo-text-medium subtext[^"]*"[^>]*>(?:<!--[^>]*-->)*([^<]*)', b)
            elemek.append((int(t.group(1)), html.unescape(c.group(1)).strip(), html.unescape(al.group(1)).strip() if al else ''))
        lat += len(elemek)
        for i, (ts, cim, alcim) in enumerate(elemek):
            if not verne_e(cim, alcim) and not cim_verne_e(alcim):
                continue
            kezd = dt.datetime.fromtimestamp(ts, dt.timezone.utc)
            veg = dt.datetime.fromtimestamp(elemek[i + 1][0], dt.timezone.utc) if i + 1 < len(elemek) else kezd + dt.timedelta(hours=1)
            if veg < MOST:
                continue
            ki.append({'tipus': 'radio', 'orszag': 'fr', 'csatorna': nev, 'cim': cim, 'alcim': alcim, 'ev': None,
                       'kezd': kezd.isoformat(), 'perc': max(1, round((veg - kezd).total_seconds() / 60)),
                       'link': f'https://www.radiofrance.fr/{adoazon}/grille-programmes?date={nap:%d-%m-%Y}'})
        time.sleep(1)
    ATNEZVE['radio-' + adoazon] = lat
    return ki


def deutschlandradio(domain, nev):
    ki, lat = [], 0
    for nap in napok():
        try:
            h = letolt(f'https://www.{domain}/programm?drsearch:date={nap:%Y-%m-%d}', 'de').decode('utf-8', 'replace')
        except Exception:
            continue
        for j in re.findall(r'data-json="([^"]+)"', h):
            try:
                d = json.loads(html.unescape(j))
                d = d.get('value') if isinstance(d, dict) else None
            except Exception:
                continue
            if not isinstance(d, dict) or d.get('__typename') != 'BroadcastLines' or not d.get('startDateRaw'):
                continue
            lat += 1
            cim, leir = d.get('title') or '', (d.get('shortText') or '') + ' ' + (d.get('pressText') or '')
            if not verne_e(cim, leir):
                continue
            kezd = dt.datetime.fromisoformat(d['startDateRaw'].replace('Z', '+00:00'))
            veg = dt.datetime.fromisoformat(d['endDateRaw'].replace('Z', '+00:00')) if d.get('endDateRaw') else kezd + dt.timedelta(hours=1)
            if veg < MOST:
                continue
            ki.append({'tipus': 'radio', 'orszag': 'de', 'csatorna': nev, 'cim': cim,
                       'alcim': (d.get('shortText') or '').split('\n')[0].strip(), 'ev': None, 'kezd': kezd.isoformat(),
                       'perc': max(1, round((veg - kezd).total_seconds() / 60)), 'link': f'https://www.{domain}/programm?drsearch:date={nap:%Y-%m-%d}'})
        time.sleep(1)
    ATNEZVE['radio-' + domain] = lat
    return ki


def oe1():
    ki, lat = [], 0
    for nap in napok():
        try:
            h = letolt(f'https://oe1.orf.at/programm/{nap:%Y%m%d}', 'de').decode('utf-8', 'replace')
        except Exception:
            continue
        elemek = re.findall(r'<span class="programTime">\s*(\d{1,2}):(\d{2})</span><a href="([^"]+)">([^<]+)</a>', h)
        lat += len(elemek)
        for i, (hh, mm, l, cim) in enumerate(elemek):
            cim = html.unescape(cim).strip()
            if not cim_verne_e(cim):
                continue
            kezd = budapest_ido(nap, int(hh), int(mm))
            veg = budapest_ido(nap, int(elemek[i + 1][0]), int(elemek[i + 1][1])) if i + 1 < len(elemek) else kezd + dt.timedelta(hours=1)
            if veg < kezd:
                veg += dt.timedelta(days=1)
            if veg < MOST:
                continue
            ki.append({'tipus': 'radio', 'orszag': 'at', 'csatorna': 'Ö1', 'cim': cim, 'alcim': '', 'ev': None,
                       'kezd': kezd.isoformat(), 'perc': max(1, round((veg - kezd).total_seconds() / 60)), 'link': 'https://oe1.orf.at' + l})
        time.sleep(1)
    ATNEZVE['radio-oe1'] = lat
    return ki


# ---------------------------------------------------------------- Egyéb események: kiállítás, koncert, fesztivál
HONAP_HU = {h: i + 1 for i, h in enumerate(['január', 'február', 'március', 'április', 'május', 'június', 'július', 'augusztus',
                                             'szeptember', 'október', 'november', 'december'])}


def port_esemenyek():
    ki, latott = [], set()
    for q in ['verne', 'jules verne', 'verne gyula', 'nemo kapitány', '80 nap alatt', 'nautilus']:
        try:
            h = letolt(PORT + '/kereso?q=' + urllib.parse.quote_plus(q) + '&type=generalevent').decode('utf-8', 'replace')
        except Exception:
            continue
        for a in re.findall(r'<article data-category="[^"]*">(.*?)</article>', h, re.S):
            c = re.search(r'<a class="title" href="([^"]+)"[^>]*>\s*([^<]+?)\s*</a>', a)
            if not c or c.group(1) in latott:
                continue
            latott.add(c.group(1))
            cim = html.unescape(c.group(2)).strip()
            leir = szoveg(re.search(r'<p class="description">(.*?)</p>', a, re.S).group(1)) if '<p class="description">' in a else ''
            if not verne_e(cim, leir):
                continue
            fajta = szoveg(re.search(r'<span class="name">([^<]+)</span>', a).group(1)) if '<span class="name">' in a else ''
            osszeg = szoveg(re.search(r'<label class="summary">(.*?)</label>', a, re.S).group(1)) if '<label class="summary">' in a else ''
            m = re.match(r'(\d{4})\. (\w+) (\d{1,2})\.(?: (\d{1,2}:\d\d))?', osszeg)
            if not m or m.group(2).lower() not in HONAP_HU:
                continue
            nap = dt.date(int(m.group(1)), HONAP_HU[m.group(2).lower()], int(m.group(3)))
            if nap < MOST.date():
                continue
            hely = re.search(r'\(([^()]+)\)\s*$', osszeg)
            ki.append({'tipus': 'egyeb', 'orszag': 'hu', 'cim': cim, 'fajta': fajta.lower(), 'hely': hely.group(1) if hely else '',
                       'varos': '', 'datum': nap.isoformat(), 'ido': m.group(4) or '', 'link': PORT + c.group(1)})
        time.sleep(1)
    return ki


# a „Jules Verne” nevet viselő helyek (iskola, könyvtár, utca) eseményei nem Verne-események – a múzeumai igen
HELYNEV = re.compile(r'(?i)(lyc[ée]e|coll[èe]ge|[ée]cole|biblioth[èe]que|m[ée]diath[èe]que|gymnase|stade|salle|rue|avenue|all[ée]e|place|quai|boulevard|centre|maison de quartier|complexe|piscine|résidence)(?: \w+){0,2} jules[- ]verne')
VERNE_HELY = re.compile(r'(?i)mus[ée]e jules[- ]verne|maison de jules[- ]verne|maison jules[- ]verne')


def unidivers():
    ki, latott = [], set()
    for q in ['jules verne', 'vingt mille lieues', 'tour du monde en 80 jours', 'capitaine nemo', 'voyage au centre de la terre']:
        try:
            h = letolt('https://unidivers.fr/?s=' + urllib.parse.quote_plus(q), 'fr').decode('utf-8', 'replace')
        except Exception:
            continue
        for l, cim in re.findall(r'<h2><a href="(https://unidivers\.fr/event/[^"]+)"[^>]*>([^<]+)</a>', h):
            if l in latott:
                continue
            latott.add(l)
            cim = html.unescape(cim).replace('\xa0', ' ').strip()
            if not (VERNE_HELY.search(cim) or (cim_verne_e(cim) and not HELYNEV.search(cim))):
                continue
            m = re.search(r'-(\d{4})-(\d{2})-(\d{2})(?:t(\d{2})(\d{2}))?', l)
            if not m:
                continue
            nap = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if nap < MOST.date():
                continue
            szinpad = re.search(r'(?i)th[ée][aâ]tre|spectacle|compagnie|\bcie\b|\bconte\b|op[ée]ra|op[ée]rette|com[ée]die musicale|marionnette|lecture', cim + ' ' + l)
            ki.append({'tipus': 'szinhaz' if szinpad else 'egyeb', 'orszag': 'fr', 'cim': cim, 'fajta': '', 'mufaj': '',
                       'hely': '', 'varos': '', 'datum': nap.isoformat(),
                       'ido': f'{m.group(4)}:{m.group(5)}' if m.group(4) else '', 'link': l})
        time.sleep(1)
    return ki


# ---------------------------------------------------------------- Párizs, Nantes, Amiens: a városok saját programnaptára
# (Verne életének három városa). Csak a dátumozott, Verne-hez kötődő programok kerülnek be; a „Jules Verne”
# nevű utcában, parkban, iskolában tartott, de Verne-hez nem kötődő események nem.
HELYNEV2 = re.compile(r'(?i)\b(?:ape|apel|amicale|association|asso|lyc[ée]e|coll[èe]ge|[ée]cole|biblioth[èe]que|m[ée]diath[èe]que|gymnase|stade|salle|rue|avenue|all[ée]e|place|'
                      r'quai|boulevard|bd|square|parc|jardin|esplanade|centre|maison de quartier|complexe|piscine|r[ée]sidence|cirque|pont|'
                      r'cit[ée]|lyc|ehpad|cr[èe]che)(?: [\w\'’-]+){0,2} jules[- ]verne')
SZINPAD = re.compile(r'(?i)th[ée][aâ]tre|spectacle|compagnie|\bcie\b|\bconte\b|op[ée]ra|op[ée]rette|com[ée]die musicale|marionnette|lecture|impro|concert')
HONAP_FR = {'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12}


def verne_program(cim, leiras=''):
    """Verne-program-e: a cím a művekre vagy Verne nevére vall, vagy a leírás Verne nevét említi
    (de nem egy róla elnevezett hely nevében)."""
    if HELYNEV2.search(cim) and not VERNE_HELY.search(cim):
        cim = HELYNEV2.sub(' ', cim)
    if cim_verne_e(cim):
        return True
    # a leírás elején (az első 300 betűben) kell Verne nevének állnia – ott, ahol a program tárgyát mondják el;
    # egy későbbi, futó említés nem elég
    t = HELYNEV2.sub(' ', szoveg(leiras or ''))[:300]
    return verne_e(cim, t)


def idoszak(d1, d2):
    return f'{d1:%d.%m.%Y} – {d2:%d.%m.%Y}' if d1 != d2 else ''


def paris():
    """Párizs: „Que faire à Paris?” – a Ville de Paris nyílt programnaptára (opendata.paris.fr)."""
    ki = []
    url = ('https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-/records?limit=100&where='
           + urllib.parse.quote('search("jules verne") and date_end >= now()'))
    d = json.loads(letolt(url, 'fr'))
    ATNEZVE['paris'] = d.get('total_count')
    for x in d.get('results', []):
        cim = html.unescape(x.get('title') or '').strip()
        if not cim or not verne_program(cim, (x.get('lead_text') or '') or (x.get('description') or '')):
            continue
        alkalmak = []
        for o in (x.get('occurrences') or '').split(';'):
            k = o.split('_')[0]
            try:
                alkalmak.append(dt.datetime.fromisoformat(k))
            except ValueError:
                pass
        jovo = sorted(a for a in alkalmak if a.date() >= MOST.date())
        try:
            eleje = dt.datetime.fromisoformat(x['date_start']).date()
            vege = dt.datetime.fromisoformat(x['date_end']).date()
        except (KeyError, TypeError, ValueError):
            continue
        kov = jovo[0] if jovo else None
        nap = kov.date() if kov else max(eleje, MOST.date())
        ido = f'{kov:%H:%M}' if kov and kov.strftime('%H:%M') not in ('00:00', '10:00') else ''
        ki.append({'tipus': 'szinhaz' if SZINPAD.search(cim + ' ' + (x.get('lead_text') or '')) else 'egyeb', 'orszag': 'fr',
                   'cim': cim, 'fajta': '', 'mufaj': '', 'hely': (x.get('address_name') or '').strip(), 'varos': 'Párizs',
                   'datum': nap.isoformat(), 'ido': ido, 'ig': vege.isoformat(), 'idoszak': idoszak(max(eleje, MOST.date()), vege),
                   'link': x.get('url') or ''})
    return ki


def nantes():
    """Nantes: a Nantes Métropole programnaptára (data.nantesmetropole.fr) – benne a Musée Jules Verne programjai."""
    url = ('https://data.nantesmetropole.fr/api/explore/v2.1/catalog/datasets/244400404_agenda-evenements-nantes-metropole_v2/records?'
           'limit=100&order_by=date&select=id_manif,nom,description_evt,date,heure_debut,lieu,ville,emetteur,types_libelles,url_site,lien_agenda,annule&where='
           + urllib.parse.quote(f'search("jules verne") and date >= date\'{MOST.date().isoformat()}\''))
    d = json.loads(letolt(url, 'fr'))
    ATNEZVE['nantes'] = d.get('total_count')
    csop = {}
    for x in d.get('results', []):
        if x.get('annule') == 'oui':
            continue
        cim = html.unescape(x.get('nom') or '').strip()
        muzeum = 'JULES VERNE' in (x.get('emetteur') or '').upper()
        if not cim or not (muzeum or verne_program(cim, x.get('description_evt') or '')):
            continue
        csop.setdefault(x.get('id_manif') or cim, []).append(x)
    ki = []
    for xs in csop.values():
        xs.sort(key=lambda x: (x.get('date') or '', x.get('heure_debut') or ''))
        x, utolso = xs[0], xs[-1]
        tipusok = ' '.join(x.get('types_libelles') or [])
        cim = html.unescape(x['nom']).strip()
        muzeum = 'JULES VERNE' in (x.get('emetteur') or '').upper()
        d1, d2 = dt.date.fromisoformat(x['date']), dt.date.fromisoformat(utolso['date'])
        ki.append({'tipus': 'szinhaz' if SZINPAD.search(cim + ' ' + tipusok) else 'egyeb', 'orszag': 'fr', 'cim': cim,
                   'fajta': (x.get('types_libelles') or [''])[0].split(' - ')[0].lower(), 'mufaj': '',
                   'hely': (x.get('lieu') or '').strip(), 'varos': (x.get('ville') or 'Nantes').strip(),
                   'datum': d1.isoformat(), 'ido': x.get('heure_debut') or '', 'ig': d2.isoformat(),
                   'idoszak': (f'{len(xs)} × · ' if len(xs) > 2 else '') + idoszak(d1, d2) if len(xs) > 1 else '',
                   'link': x.get('url_site') or x.get('lien_agenda') or ''})
    return ki


def fr_datumok(t):
    """Francia dátumok egy szövegből: „Du 3 juillet 2026 au 11 janvier 2027”, „Le 22 avril 2026”, „22/04/2026”."""
    ki = []
    for n, h, e in re.findall(r'(?i)\b(\d{1,2})(?:er)?\s+(janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[uû]t|septembre|octobre|novembre|d[ée]cembre)\s+(\d{4})', t):
        try:
            ki.append(dt.date(int(e), HONAP_FR[h.lower().replace('û', 'u')], int(n)))
        except (KeyError, ValueError):
            pass
    for n, h, e in re.findall(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', t):
        try:
            ki.append(dt.date(int(e), int(h), int(n)))
        except ValueError:
            pass
    return ki


def amiens():
    """Amiens: az amiens.fr eseménynaptára – a teljes lista Verne-tételei (benne a Maison de Jules Verne programjai)."""
    ki, latott, lapok = [], set(), 1
    oldal = 1
    while oldal <= lapok and oldal <= 80:
        h = letolt('https://www.amiens.fr/Les-evenements' + (f'/(page)/{oldal}' if oldal > 1 else ''), 'fr').decode('utf-8', 'replace')
        if oldal == 1:
            lapok = max([1] + [int(x) for x in re.findall(r'/Les-evenements/\(page\)/(\d+)', h)])
        for blokk in h.split('diary-block jsBlockLink')[1:]:
            lc = re.search(r'href="(/Les-evenements/[^"(#]+)"[^>]*class="diary-block__content-hidden__title"[^>]*>\s*(.*?)\s*</a>', blokk, re.S) \
                or re.search(r'class="diary-block__content-hidden__title"[^>]*href="(/Les-evenements/[^"(#]+)"[^>]*>\s*(.*?)\s*</a>', blokk, re.S)
            if not lc or lc.group(1) in latott:
                continue
            l = lc.group(1)
            latott.add(l)
            cim = szoveg(lc.group(2))
            if not (VERNE_HELY.search(cim) or verne_program(cim) or VERNE_HELY.search(szoveg(blokk[:6000]))):
                continue
            e = letolt('https://www.amiens.fr' + l, 'fr').decode('utf-8', 'replace')
            t = szoveg(re.sub(r'(?s)<(header|nav|footer)[^>]*>.*?</\1>', ' ', e))
            napok = sorted(set(fr_datumok(t)))
            jovo = [n for n in napok if n >= MOST.date()]
            if not jovo:
                continue
            ki.append({'tipus': 'szinhaz' if SZINPAD.search(cim) else 'egyeb', 'orszag': 'fr', 'cim': cim.replace(' | ', ' – '),
                       'fajta': '', 'mufaj': '', 'hely': 'Maison de Jules Verne' if 'jules verne' in t.lower() and 'maison de jules verne' in t.lower() else '',
                       'varos': 'Amiens', 'datum': max(napok[0], MOST.date()).isoformat(), 'ido': '', 'ig': napok[-1].isoformat(),
                       'idoszak': idoszak(max(napok[0], MOST.date()), napok[-1]), 'link': 'https://www.amiens.fr' + l})
            time.sleep(1)
        oldal += 1
        time.sleep(0.5)
    ATNEZVE['amiens'] = len(latott)
    return ki


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


# ---------------------------------------------------------------- Külföldi mozik: „most a mozikban” listák
def mozi_lista(orszag, oldalak, minta, alap, kozos_link=None, cim_fn=None):
    """Egy ország „most a mozikban” listája: (link, cím) párok egy regexszel; csak a Verne-címek maradnak."""
    ki, latott = [], set()
    for u in oldalak:
        try:
            h = letolt(u, orszag).decode('utf-8', 'replace')
        except Exception:
            if not latott:
                raise
            break
        uj = 0
        for x in re.findall(minta, h, re.S):
            l, cim = x if isinstance(x, tuple) else ((x, x) if cim_fn else (None, x))
            cim = cim_fn(l, cim) if cim_fn else html.unescape(re.sub(r'\s+', ' ', cim)).strip()
            if not cim or cim in latott:
                continue
            latott.add(cim)
            uj += 1
            if cim_verne_e(cim):
                ki.append({'tipus': 'mozi', 'orszag': orszag, 'cim': cim, 'ev': None, 'helyek': [],
                           'link': (alap + l if l and l.startswith('/') else (l or kozos_link or u))})
        if not uj:
            break
        time.sleep(1)
    ATNEZVE['mozi-' + orszag] = len(latott)
    return ki


def filmweb_cim(l, _):
    m = re.match(r'/film/(.+)-\d{4}-\d+$', urllib.parse.unquote_plus(l or ''))
    return m.group(1).strip() if m else ''


KULFOLDI_MOZIK = [
    ('sensacine.com', 'es', [f'https://www.sensacine.com/peliculas/en-cartelera/cines/' + (f'?page={i}' if i > 1 else '') for i in range(1, 20)],
     r'<a class="meta-title-link" href="([^"]+)"[^>]*>([^<]+)</a>', 'https://www.sensacine.com', None, None),
    ('picturehouses.com', 'uk', ['https://www.picturehouses.com/whats-on'], r'<h3[^>]*>([^<]{2,120})</h3>', '',
     'https://www.picturehouses.com/whats-on', None),
    ('filmweb.pl', 'pl', ['https://www.filmweb.pl/showtimes'], r'href="(/film/[^"]+)"', 'https://www.filmweb.pl', None, None),
    ('film.at', 'at', ['https://www.film.at/kinoprogramm'], r'<h\d[^>]*>([^<]{2,120})</h\d>', '', 'https://www.film.at/kinoprogramm', None),
    ('rottentomatoes.com', 'us', ['https://www.rottentomatoes.com/browse/movies_in_theaters/'],
     r'data-qa="discovery-media-list-item-title"[^>]*>\s*([^<]+?)\s*<', '', 'https://www.rottentomatoes.com/browse/movies_in_theaters/', None),
]


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
    eredmeny = {'frissitve': MOST.replace(microsecond=0).isoformat(), 'tv': [], 'radio': [], 'szinhaz': [], 'mozi': [], 'egyeb': [],
                'forrasok': {}}

    def fut(nev, f):
        t0 = time.time()
        try:
            r = f()
            eredmeny['forrasok'][nev] = {'ok': True, 'db': sum(len(x) for x in r) if isinstance(r, tuple) else len(r),
                                         'mp': round(time.time() - t0)}
            if nev == 'port.hu tévékereső':
                eredmeny['forrasok'][nev]['atnezve'] = ATNEZVE.get('tévékereső')
                eredmeny['forrasok'][nev]['verne'] = ATNEZVE.get('tévékereső-verne')
            for kk, ak in [('France Culture', 'radio-franceculture'), ('France Inter', 'radio-franceinter'), ('Deutschlandfunk Kultur', 'radio-deutschlandfunkkultur.de'), ('Deutschlandfunk', 'radio-deutschlandfunk.de'), ('Ö1', 'radio-oe1')]:
                if nev == kk and ak in ATNEZVE:
                    eredmeny['forrasok'][nev]['atnezve'] = ATNEZVE[ak]
            if nev == 'ticketmaster' and 'ticketmaster-proba' in ATNEZVE:
                eredmeny['forrasok'][nev]['proba'] = ATNEZVE['ticketmaster-proba']
            if 'radio-' + nev.split()[-1] in ATNEZVE and ATNEZVE['radio-' + nev.split()[-1]]:
                eredmeny['forrasok'][nev]['radio'] = ATNEZVE['radio-' + nev.split()[-1]]
            if nev.split()[-1] in ATNEZVE:
                eredmeny['forrasok'][nev]['atnezve'] = ATNEZVE[nev.split()[-1]]
            return r
        except Exception as e:  # a forrás hibája nem állítja meg a többit
            eredmeny['forrasok'][nev] = {'ok': False, 'hiba': str(e)[:200], 'mp': round(time.time() - t0)}
            return ([], []) if nev == 'port.hu' else []

    for orszag, cimke in EPG:
        nev = 'iptvx.one RU' if cimke.startswith('http') else 'epgshare01 ' + cimke
        for m in fut(nev, lambda o=orszag, c=cimke: epg_orszag(o, c)):
            eredmeny[m.pop('tipus')].append(m)
    for nev, f in [('France Culture', lambda: radiofrance('franceculture', 'France Culture')),
                   ('France Inter', lambda: radiofrance('franceinter', 'France Inter')),
                   ('Deutschlandfunk Kultur', lambda: deutschlandradio('deutschlandfunkkultur.de', 'Deutschlandfunk Kultur')),
                   ('Deutschlandfunk', lambda: deutschlandradio('deutschlandfunk.de', 'Deutschlandfunk')),
                   ('Ö1', oe1)]:
        for m in fut(nev, f):
            eredmeny[m.pop('tipus')].append(m)
    eredmeny['egyeb'] += fut('port.hu események', port_esemenyek)
    for m in fut('unidivers.fr', unidivers):
        eredmeny[m['tipus']].append(m)
    for m in fut('port.hu tévé', port_tv):  # (a port.hu tévéműsor-keresője a GitHubról nem ad megbízható találatot – kimaradt)
        eredmeny[m.pop('tipus')].append(m)
    sz, mo = fut('port.hu', port_hu)
    eredmeny['szinhaz'] += sz
    eredmeny['mozi'] += mo
    for nev, f in [('Párizs (opendata.paris.fr)', paris), ('Nantes (data.nantesmetropole.fr)', nantes), ('Amiens (amiens.fr)', amiens)]:
        for m in fut(nev, f):
            eredmeny[m['tipus']].append(m)
        kulcs = nev.split()[0].lower().replace('á', 'a')
        if kulcs in ATNEZVE:
            eredmeny['forrasok'][nev]['atnezve'] = ATNEZVE[kulcs]
    eredmeny['szinhaz'] += fut('atgtickets.com', atg)
    eredmeny['szinhaz'] += fut('offi.fr', offi)
    eredmeny['mozi'] += fut('allocine.fr', allocine)
    eredmeny['mozi'] += fut('comingsoon.it', comingsoon)
    for nev, o, oldalak, minta, alap, kozos, _ in KULFOLDI_MOZIK:
        cfn = filmweb_cim if nev == 'filmweb.pl' else None
        eredmeny['mozi'] += fut(nev, lambda o=o, ol=oldalak, mi=minta, a=alap, k=kozos, c=cfn: mozi_lista(o, ol, mi, a, k, c))
        if 'mozi-' + o in ATNEZVE:
            eredmeny['forrasok'][nev]['atnezve'] = ATNEZVE['mozi-' + o]
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
    for m in eredmeny['szinhaz'] + eredmeny['mozi'] + eredmeny['egyeb']:
        m.pop('tipus', None)
    for k in ('szinhaz', 'egyeb'):  # ugyanaz az esemény két forrásból (pl. Unidivers és a város naptára): a részletesebb marad
        lista = eredmeny[k]
        kidob = set()
        for i, a in enumerate(lista):
            for j, b in enumerate(lista):
                if i >= j or i in kidob or j in kidob or not a.get('datum') or a.get('datum') != b.get('datum'):
                    continue
                ea, eb = egyszerusit(a['cim']).strip(), egyszerusit(b['cim']).strip()
                if min(len(ea), len(eb)) >= 12 and (ea in eb or eb in ea or ea[:24] == eb[:24]):
                    kidob.add(j if (a.get('hely') or a.get('ido')) else i)
        eredmeny[k] = [m for i, m in enumerate(lista) if i not in kidob]
    egy = {}
    for m in eredmeny['egyeb']:  # ugyanaz az esemény kétszer (kicsit más címmel) – egyszer
        egy.setdefault((m.get('datum'), egyszerusit(m['cim'])[:32]), m)
    eredmeny['egyeb'] = list(egy.values())
    eredmeny['egyeb'].sort(key=lambda m: (m.get('datum') or '9999', m.get('ido') or '', m['orszag'], m['cim']))
    eredmeny['szinhaz'].sort(key=lambda m: (m.get('datum') or '9999', m['orszag'], m['cim']))
    eredmeny['mozi'].sort(key=lambda m: (m['orszag'] != 'hu', m['orszag'], m['cim']))

    os.makedirs(os.path.dirname(ki_fajl) or '.', exist_ok=True)
    with open(ki_fajl, 'w', encoding='utf-8') as f:
        json.dump(eredmeny, f, ensure_ascii=False, indent=1)
    for k in ('tv', 'radio', 'szinhaz', 'mozi', 'egyeb'):
        print(f'{k}: {len(eredmeny[k])}')
    for n, f in eredmeny['forrasok'].items():
        print(n, f)


if __name__ == '__main__':
    main()
