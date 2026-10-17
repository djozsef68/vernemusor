# Mi számít Verne-műsornak? – a szűrő kulcsszavai.
# Az összevetés ékezet és kis-nagybetű nélkül történik, a számok elválasztói nélkül
# (20 000 = 20.000 = 20,000 = 20000). Új címet egyszerűen egy új sorral lehet felvenni.
import re
import unicodedata


def egyszerusit(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace('ß', 'ss').replace('œ', 'oe').replace('æ', 'ae')
    s = re.sub(r'(\d)[\s.,  ](?=\d{3}\b)', r'\1', s)
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return ' ' + s.strip() + ' '


# Verne neve – ez a leírásban is elég (pl. „Rádiószínház … Verne Gyula regénye nyomán”).
NEV = [
    r'jules vernes?', r'jules verne s', r'verne gyula', r'gyula verne', r'verne gy', r'giulio verne', r'guilio verne', r'gulio verne',
    r'julio verne', r'julius verne', r'juliusz verne', r'jules gabriel verne', r'jule verne', r'verne jules', r'verne julius',
    r'zsul vern', r'jules vern', r'jul vern', r'jules verns?',
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
    # Offenbach Verne nyomán: Utazás a Holdba (Le voyage dans la lune), Doktor Ox (Le docteur Ox)
    r'ox doktor', r'doktor ox', r'docteur ox', r'dottor ox', r'doctor ox', r'reise (?:in|auf) den mond',
    r'viaggio nella luna', r'trip to the moon', r'voyage to the moon',
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
]

# Ami hasonlít, de nem Verne.
TILTO = [
    r'nemo nyomaban', r'finding nemo', r'monde de nemo', r'findet nemo', r'ricerca di nemo', r'szenilla', r'finding dory',
    r'verne troyer', r'verne lundquist', r'little nemo', r'nemo the', r'8 jours de la terre',
]

_NEV = re.compile(r' (?:' + '|'.join(NEV) + r') ')
_CIM = re.compile(r' (?:' + '|'.join(CIM) + r') ')
_TILTO = re.compile(r' (?:' + '|'.join(TILTO) + r') ')


def verne_e(cim, *egyeb):
    """Igaz, ha a cím (vagy az alcím/leírás Verne neve miatt) Verne-műsorra vall."""
    c = egyszerusit(cim)
    if _TILTO.search(c):
        return False
    if _CIM.search(c) or _NEV.search(c):
        return True
    for e in egyeb:
        e = egyszerusit(e)
        if _TILTO.search(e):
            return False
        if _NEV.search(e):
            return True
    return False


def cim_verne_e(cim):
    c = egyszerusit(cim)
    return not _TILTO.search(c) and bool(_CIM.search(c) or _NEV.search(c))
