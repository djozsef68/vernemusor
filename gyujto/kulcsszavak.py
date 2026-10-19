# Mi számít Verne-műsornak? – a szűrő kulcsszavai.
# Az összevetés ékezet és kis-nagybetű nélkül történik, a számok elválasztói nélkül
# (20 000 = 20.000 = 20,000 = 20000). Új címet egyszerűen egy új sorral lehet felvenni.
import re
import unicodedata


def egyszerusit(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace('ß', 'ss').replace('œ', 'oe').replace('æ', 'ae').replace('ł', 'l').replace('ø', 'o').replace('ё', 'е')
    s = re.sub(r'(\d)[\s.,  ](?=\d{3}\b)', r'\1', s)
    s = re.sub(r'[^a-z0-9\u0430-\u044f]+', ' ', s)  # latin és cirill betűk, számok
    return ' ' + s.strip() + ' '


# Verne neve – ez a leírásban is elég (pl. „Rádiószínház … Verne Gyula regénye nyomán”).
NEV = [
    r'jules vernes?', r'jules verne s', r'verne gyula', r'gyula verne', r'verne gy', r'giulio verne', r'guilio verne', r'gulio verne',
    r'julio verne', r'julius verne', r'juliusz verne', r'jules gabriel verne', r'jule verne', r'verne jules', r'verne julius',
    r'zsul vern', r'jules vern', r'jul vern', r'jules verns?',
    r'julesa? verna', r'julesa vernea', r'julese verna',  # cseh, szlovák, horvát birtokos eset („podle Julese Verna”)
    r'жюл[ья]? верн\w*', r'жюль верн', r'верн жюль',
]

# Művek és szereplők – a címben (a sorozatcím mellett az epizódcímben is).
CIM = [
    r'verne',  # a címben magában is elég (Verne-est, Verne és a tenger …); a leírásban csak a teljes név számít
    # magyar
    r'nemo kapitany', r'kapitany nemo', r'(?:husz|20)\s?ezer merfold', r'20000 merfold', r'30000 merfold',
    r'(?:nyolcvan|80) nap alatt', r'utazas a fold kozeppontja', r'utazas a holdba', r'a foldtol a holdig',
    r'rejtelmes sziget', r'ketevi vakacio', r'grant kapitany', r'sandor matyas', r'sztrogof+\w*', r'tizenot eves kapitany',
    r'dunai hajos', r'dunai revkalauz', r'karpati kastely', r'varkastely a karpatokban', r'uszo varos',
    r'robur a hodito', r'a vilag ura', r'(?:a )?begum otszazmilli\w*', r'ot het leghajon', r'hatteras kapitany',
    r'antifer mester', r'keraban\w*', r'az acelvaros titka', r'ordogi talalmany', r'az ustokoson', r'fekete india',
    r'jegszfinx', r'willy fog', r'phileas fogg',
    # spanyol
    r'vuelta al mundo en (?:80|ochenta) dias', r'viaje al centro de la tierra', r'(?:20000|veinte mil) leguas',
    r'miguel strogoff', r'de la tierra a la luna', r'alrededor de la luna', r'cinco semanas en globo',
    r'dos anos de vacaciones', r'hijos del capitan grant', r'capitan nemo', r'capitan de quince anos',
    r'faro del fin del mundo', r'robur el conquistador', r'senor del mundo', r'castillo de los carpatos',
    # portugál
    r'volta ao mundo em (?:80|oitenta) dias', r'viagem ao centro da terra', r'ilha misteriosa', r'(?:20000|vinte mil) leguas',
    r'da terra a lua', r'cinco semanas (?:em um|num) balao', r'dois anos de ferias', r'filhos do capitao grant',
    r'capitao nemo', r'capitao de quinze anos', r'farol do fim do mundo',
    # lengyel
    r'w (?:80|osiemdziesiat) dni dookola swiata', r'dookola swiata w (?:80|osiemdziesiat) dni', r'podroz do wnetrza ziemi',
    r'tajemnicza wyspa', r'(?:20000|dwadziescia tysiecy) mil podmorskiej', r'michal strogow', r'z ziemi na ksiezyc',
    r'piec tygodni w balonie', r'dwa lata wakacji', r'dzieci kapitana granta', r'pietnastoletni kapitan',
    r'latarnia na krancu swiata', r'robur zdobywca', r'zamek w karpatach',
    # orosz
    r'вокруг света за (?:80|восемьдесят) дней', r'таинственный остров', r'дети капитана гранта',
    r'(?:20000|двадцать тысяч) лье', r'михаил строгов', r'капитан немо', r'путешествие к центру земли',
    r'с земли на луну', r'пятнадцатилетний капитан', r'пять недель на воздушном шаре', r'робур завоеватель',
    r'властелин мира', r'матиас шандор', r'замок в карпатах', r'маяк на краю света', r'два года каникул',
    r'в поисках потерпевших кораблекрушение', r'гектор сервадак',
    # Offenbach Verne nyomán: Utazás a Holdba (Le voyage dans la lune), Doktor Ox (Le docteur Ox)
    r'ox doktor', r'doktor ox', r'docteur ox', r'dottor ox', r'doctor ox', r'reise (?:in|auf) den mond',
    r'viaggio nella luna', r'trip to the moon', r'voyage to the moon',
    r'egy kinai viszontagsagai', r'tribulations d un chinois', r'tribulations of a chinaman', r'tribulations in china',
    r'cinese in cina', r'leiden eines chinesen',
    # angol
    r'around the world in (?:80|eighty) days', r'(?:20000|30000|twenty thousand) leagues', r'000 leagues under',
    r'journey to the cent(?:er|re) of the earth', r'from the earth to the moon', r'mysterious island',
    r'in search of the castaways', r'michael strogoff', r'five weeks in a balloon', r'master of the world',
    r'robur the conqueror', r'light at the edge of the world', r'two years (?:s )?vacation', r'captain nemo',
    r'castle (?:in|of) the carpathians', r'off on a comet', r'begum s fortune', r'captain at fifteen', r'dick sand',
    # francia
    r'tour du monde en (?:80|quatre vingts?) jours', r'(?:20000|vingt mille) lieues', r'voyage au centre de la terre',
    r'de la terre a la lune', r'autour de la lune', r'ile mysterieuse', r'enfants du capitaine grant', r'michel strogoff',
    r'cinq semaines en ballon', r'deux ans de vacances', r'mathias sandorf', r'phare du bout du monde',
    r'capitaine de quinze ans', r'chateau des carpathes', r'robur le conquerant', r'maitre du monde', r'indes noires',
    r'keraban le tetu', r'pilote du danube', r'sphinx des glaces', r'voyages extraordinaires', r'capitaine nemo',
    r'hector servadac', r'la jangada', r'voyage dans la lune', r'naufrages du fol espoir', r'nord contre sud',
    # német
    r'in 80 tagen um die welt', r'um die (?:erde|welt) in 80 tagen', r'(?:20000|zwanzigtausend) meilen unter',
    r'reise zum mittelpunkt der erde', r'von der erde zum mond', r'die geheimnisvolle insel', r'kinder des kapitan grant',
    r'kurier des zaren', r'funf wochen im ballon', r'zwei jahre ferien', r'kapitan nemo', r'karpatenschloss',
    r'leuchtturm am ende der welt', r'robur der eroberer',
    # olasz
    r'giro del mondo in (?:80|ottanta) giorni', r'(?:20000|ventimila) leghe', r'viaggio al centro della terra',
    r'dalla terra alla luna', r'isola misteriosa', r'figli del capitano grant', r'michele strogoff',
    r'cinque settimane in pallone', r'due anni di vacanze', r'capitano nemo', r'faro in capo al mondo',
    r'castello dei carpazi',
    # cseh (Karel Zeman Verne-filmjei is: Vynález zkázy, Ukradená vzducholoď, Na kometě)
    r'(?:20000|dvacet tisic) mil pod morem', r'cesta kolem sveta za (?:80|osmdesat) dni', r'cesta do stredu zeme',
    r'tajuplny ostrov', r'deti kapitana granta', r'patnactilety kapitan', r'michal strogov', r'caruv kuryr',
    r'ze zeme na mesic', r'cesta kolem mesice', r'pet nedel v balone', r'dva roky prazdnin', r'robur dobyvatel',
    r'hrad v karpatech', r'majak na konci sveta', r'matyas sandorf', r'kapitan nemo',
    r'vynalez zkazy', r'ukradena vzducholod', r'na komete', r'ocelove mesto', 
    # szlovák
    r'(?:20000|dvadsattisic|dvadsat tisic) mil pod morom', r'cesta okolo sveta za (?:80|osemdesiat) dni',
    r'zahadny ostrov', r'patnastrocny kapitan', r'zo zeme na mesiac', r'pat tyzdnov v balone', r'dva roky prazdnin',
    r'hrad v karpatoch', r'majak na konci sveta',
    # román
    r'(?:20000|douazeci de mii) de leghe sub mari', r'ocolul pamantului in (?:80|optzeci) de zile', r'ocolul lumii in (?:80|optzeci) de zile',
    r'calatorie spre centrul pamantului', r'insula misterioasa', r'copiii capitanului grant', r'capitan de cincisprezece ani',
    r'mihail strogoff', r'de la pamant la luna', r'in jurul lunii', r'cinci saptamani in balon', r'doi ani de vacanta',
    r'castelul din carpati', r'pilotul de pe dunare', r'pilotul dunarii', r'claudius bombarnac', r'capitanul nemo',
    r'farul de la capatul lumii', r'stapanul lumii', r'robur cuceritorul',
    # horvát (és szerb latin betűvel)
    r'(?:20000|dvadeset tisuca) milja pod morem', r'put oko svijeta za (?:80|osamdeset) dana', r'put oko sveta za (?:80|osamdeset) dana',
    r'put u srediste zemlje', r'tajanstveni otok', r'tajanstveno ostrvo', r'djeca kapetana granta', r'deca kapetana granta',
    r'petnaestogodisnji kapetan', r'mihajlo strogov', r'mihail strogov', r'carev glasnik', r'sa zemlje na mjesec',
    r'sa zemlje na mesec', r'pet tjedana u balonu', r'pet nedelja u balonu', r'dvije godine (?:ferija|praznika)',
    r'kapetan nemo', r'matija sandorf', r'svjetionik na kraju svijeta', r'dvorac u karpatima',
]

# Ami hasonlít, de nem Verne.
TILTO = [
    r'nemo nyomaban', r'finding nemo', r'monde de nemo', r'findet nemo', r'ricerca di nemo', r'szenilla', r'finding dory',
    r'verne troyer', r'verne lundquist', r'в поисках немо', r'buscando a nemo', r'procurando nemo', r'gdzie jest nemo',
    r'restaurant le jules verne', r'le jules verne restaurant', r'jules verne restaurant', r'hleda se nemo', r'hlada sa nemo', r'potraga za nemom', r'u potrazi za nemom', r'in cautarea lui nemo', r'nagi instynkt', r'naked and afraid', r'губка боб', r'шоу патрика', r'patrick star', r'spongebob', r'тесла', r'tesla',
    r'экстремальные динозавры', r'лесная команда', r'waldtruppe', r'little nemo', r'nemo the', r'8 jours de la terre',
]

def _minta(lista):  # a minták is ugyanúgy egyszerűsödnek, mint a szöveg (й → и, ё → е)
    return re.compile(r' (?:' + '|'.join(x.replace('й', 'и').replace('ё', 'е') for x in lista) + r') ')


_NEV = _minta(NEV)
_CIM = _minta(CIM)
_TILTO = _minta(TILTO)


def verne_e(cim, *egyeb):
    """Igaz, ha a cím (vagy az alcím/leírás Verne neve miatt) Verne-műsorra vall."""
    c = egyszerusit(cim)
    if _TILTO.search(c):
        return False
    if _CIM.search(c) or _NEV.search(c) or _NAUTILUS.match(c):
        return True
    for e in egyeb:
        e = egyszerusit(e)
        if _TILTO.search(e):
            return False
        if _NEV.search(e):
            return True
    return False


# A puszta „Nautilus” cím (a 2024-es Nemo-sorozat) – csak ha a cím maga ez, epizódjelöléssel együtt;
# a USS Nautilusról vagy a Nautilus nevű cégekről szóló műsorok így nem kerülnek be.
_NAUTILUS = re.compile(r'^ nautilus (?:(?:s\d+ ?e\d+|\d+|evad|saison|staffel|season|stagione|temporada)\b.*)?$')


def cim_verne_e(cim):
    c = egyszerusit(cim)
    return not _TILTO.search(c) and bool(_CIM.search(c) or _NEV.search(c) or _NAUTILUS.match(c))
