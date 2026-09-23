# All AR Sammlung

Private PWA fuer die japanische Pokemon-AR-Sammlung.

## Datenregel

Die App nimmt **nur**:

1. japanische Karten, deren offizielle japanische Datenbank die Rarity `rare_ar` meldet;
2. japanische Promo-Karten, die auf Bulbapedias Seite `Art_Rare` als zugehoerige Illustration-/Art-Rare-Promos gefuehrt werden.

Damit werden normale R/RR, Energy, SR, SAR und CHR nicht ueber Nummernbereiche geraten, sondern explizit ausgeschlossen.

Quellen fuer den Build:
- offizielle Japan-Daten ueber `type-null/PTCG-database` (dessen JP-Scraper pokemon-card.com nutzt)
- Bulbapedia `Art_Rare` fuer englische Namen und die Promo-Zuordnung

## GitHub

1. Neues Repo `all-ar-sammlung` erstellen und **Private** waehlen.
2. Den Inhalt dieses Ordners hochladen.
3. Unter Actions den Workflow **Update verified AR data** einmal manuell starten.
4. Danach ist `data/cards.json` mit der geprueften Liste gefuellt.

## App auf dem Handy

Eine PWA braucht HTTPS. Fuer ein wirklich privates Repo ist GitHub Pages nicht automatisch die beste Loesung, weil Pages je nach Plan/Sichtbarkeit nicht privat bereitgestellt wird. Alternativen: lokal auf dem Handy hosten oder spaeter einen privaten Hostingweg verwenden.

Besitzstatus (`Habe ich`, `Fehlt`, `Unsicher`) wird **nur im Browser auf dem Handy** in `localStorage` gespeichert. Backup/Import ist in der App enthalten.

## Ordner

5 x 4 = 20 Karten pro Seite. Erste Seite nur rechts, danach Doppelseiten mit 40 Karten.
