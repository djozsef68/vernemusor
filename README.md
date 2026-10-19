# Verne-műsorfüzet

A [Nautilus / Nemo](https://nautilus.djp.hu/) webhely **Online műsorfüzetének** adatforrása.

Minden nap egyszer (és kézzel bármikor: *Actions → Napi műsorgyűjtés → Run workflow*) lefut a
`gyujto/gyujt.py`, és a `data/musor.json` fájlba összegyűjti a következő napok Verne-műsorait:

| Fül | Forrás | Országok |
|---|---|---|
| Tévé, rádió | [epgshare01](https://epgshare01.online/) (az [iptv-org/epg](https://github.com/iptv-org/epg) egyik forrása) | HU, FR, UK, DE, IT, ES, PT, PL, CH, BE, NL, SE, NO, DK, FI, BG, TR, US, CA, MX, BR, AR, CL, CO, PE, UY, ZA, AU, NZ, CZ, SK, RO, HR, RS (a cseh–balkáni ötnél csak a helyi adók; a latin-amerikai és az északi régiós csatornák műsora egyszer) |
| Rádió | Radio France, Deutschlandfunk, Ö1, BBC Radio 4 / 4 Extra / 3 (heti műsorrend) | FR, DE, AT, UK |
| Színház · opera · operett | port.hu, jegy.hu, ATG Tickets, Offi, Unidivers, Ticketmaster | HU, UK, FR, US, CA, MX … |
| Online (nézhető) | arte.tv – Verne-dokumentumfilmek és -filmek, a nézhetőség végével | FR/DE |
| Verne városai (színház, kiállítás, egyéb) | [Que faire à Paris](https://opendata.paris.fr/explore/dataset/que-faire-a-paris-/) (Párizs nyílt adat), [Nantes Métropole programnaptára](https://data.nantesmetropole.fr/) (benne a Musée Jules Verne), [amiens.fr](https://www.amiens.fr/Les-evenements) | Párizs, Nantes, Amiens |
| Mozi | port.hu, AlloCiné, ComingSoon | HU, FR, IT |

Opcionális: ha a repó *Settings → Secrets and variables → Actions* részében van egy `TICKETMASTER_KULCS`
nevű titok (ingyenes kulcs: developer.ticketmaster.com), a Ticketmaster eseményei is bekerülnek.

A szűrő kulcsszavai: `gyujto/kulcsszavak.py` – új cím egy új sorral felvehető.
A műsoradatok a források tulajdonai; a fájl csak a Verne-tételeket tartalmazza, forrásmegjelöléssel.

A webhely a fájlt innen olvassa:
`https://raw.githubusercontent.com/djozsef68/vernemusor/main/data/musor.json`
