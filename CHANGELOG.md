# Changelog

Formát podle [Keep a Changelog](https://keepachangelog.com/cs/1.1.0/), verze podle [SemVer](https://semver.org/lang/cs/):
**MAJOR**.MINOR.PATCH – minor = nová funkce, patch = oprava.

## [1.2.0] – 2026-10-08
### Přidáno
- Ikona v záložce prohlížeče (favicon): modrá dálniční cedule s budíkem.

## [1.1.0] – 2026-10-07
### Přidáno
- Číslo verze v okně Nastavení a v konzoli při startu.
- Palivo v plánu cesty: kolik litrů chybí do cíle a kde dojde, případně kolik zbyde v cíli.

## [1.0.0] – 2026-10-06
První verzovaná verze. Obsahuje:
- Lokální dashboard pro ETS2 a ATS nad pluginem scs-sdk-plugin (jen localhost, bez spojení ven).
- Cedule s cílem, zbývající vzdáleností, reálným a herním ETA, průběh trasy.
- Jízda: rychlost s barvami a pulzem nad limitem, tempomat, kontrolky jako ikony, palivo, AdBlue.
- Odpočinek a plán: čas do pauzy s pulzem při upozornění, spánek cestou, rezerva do termínu.
- Vůz: opotřebení tahače a návěsu, provozní hodnoty, detekce nárazů.
- Relace (automatický reset při spuštění hry), log událostí, historie zakázek v SQLite.
- Souhrn po doručení s hodnocením stylu jízdy (navazuje i po restartu hry).
- Nastavení: čeština / angličtina, měna a kurz a jednotky zvlášť pro ETS2 a ATS.
- Automatické spouštění se hrou přes parametry spuštění ve Steamu.
