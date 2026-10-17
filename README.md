# Verne-műsorfüzet

A [Nautilus / Nemo](https://nautilus.djp.hu/) webhely **Online műsorfüzetének** adatforrása.

Minden nap egyszer (és kézzel bármikor: *Actions → Napi műsorgyűjtés → Run workflow*) lefut a
`gyujto/gyujt.py`, és a `data/musor.json` fájlba összegyűjti a következő napok Verne-műsorait:

| Fül | Forrás | Országok |
|---|---|---|
| Tévé, rádió | [epgshare01](https://epgshare01.online/) (az [iptv-org/epg](https://github.com/iptv-org/epg) egyik forrása) | HU, FR, UK, DE, IT |
| Színház · opera · operett | port.hu, ATG Tickets, Offi | HU, UK, Párizs |
| Mozi | port.hu, AlloCiné, ComingSoon | HU, FR, IT |

Opcionális: ha a repó *Settings → Secrets and variables → Actions* részében van egy `TICKETMASTER_KULCS`
nevű titok (ingyenes kulcs: developer.ticketmaster.com), a Ticketmaster eseményei is bekerülnek.

A szűrő kulcsszavai: `gyujto/kulcsszavak.py` – új cím egy új sorral felvehető.
A műsoradatok a források tulajdonai; a fájl csak a Verne-tételeket tartalmazza, forrásmegjelöléssel.

A webhely a fájlt innen olvassa:
`https://raw.githubusercontent.com/djozsef68/vernemusor/main/data/musor.json`
