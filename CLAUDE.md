# Palubka – kontext projektu

Lokální dashboard na druhý monitor pro Euro Truck Simulator 2 a American Truck Simulator.
Autor: TheAzerCZ (Jakub). Repo: https://github.com/TheAzerCZ/ExternalDashboard (veřejné, GPL-3.0).
Komunikace s autorem česky. Autor je z IT/security, má řidičák na kamion, preferuje jednoduchá řešení
bez zbytečného hrocení (žádný changelog, žádné složité release procesy).

## Architektura

- `dash.py`: jediný backend, **jen standardní knihovna Pythonu 3.9+** (volitelně `hidapi` pro volant).
  - čte sdílenou paměť `Local\SCSTelemetry` z pluginu RenCloud/scs-sdk-plugin (DLL v `Install files/`),
    parser `parse()` je port rozložení z kniffen/TruckSim-Telemetry (plugin v1.12), offsety jsou absolutní (`r.at(...)`),
  - `Processor.tick()` 10× za sekundu: události (pokuty, mýtné, trajekty, doručení), statistiky relace,
    detekce nárazů, hodnocení stylu jízdy, view model `_build()` pro frontend,
  - HTTP server jen na `127.0.0.1:8088` (kontrola Host hlavičky proti DNS rebindingu,
    POST vyžaduje hlavičku `X-Dash: 1`): `/` HTML, `/events` SSE stream (4×/s), `/api/history`,
    `/api/reset`, `/api/settings`, `/api/update`,
  - `Updater`: GitHub Releases (`releases/latest`), stahuje soubory z `UPDATE_FILES` přes
    raw.githubusercontent.com pod tagem releasu, záloha do `backup/<verze>/`, restart procesu,
  - `WheelLeds`: RPM diody Logitech G29/G27 přes HID, příkaz `[0x00, 0xF8, 0x12, maska, 0, 0, 0, 0x01]`.
    **Funguje jen herní rozhraní (usage_page 0x01, usage 0x04)**, vendor rozhraní 0xFF00 zápis odmítá.
    Stav se posílá znovu každých 0,5 s (G HUB ho umí přepsat). Ověřeno na skutečném G29.
  - `--demo` = simulovaná data bez hry (na vývoj UI), `--exit-with-game` = vypnout po zavření hry.
- `dashboard.html`: celé UI v jednom souboru (HTML+CSS+JS, bez knihoven). Texty přes slovník `I18N`
  (cs/en), formátování přes helpery `money()`, `dist()`, `spd()`, `vol()`, `temp()` (měny a jednotky
  zvlášť pro ETS2/ATS). Písmo Bahnschrift (Windows), vzhled dálničních cedulí.
- `dashboard-start.bat` ruční spuštění, `game-start.bat` pro Steam Launch Options (`pythonw`, bez okna,
  log do `dash.log`).

## Osobní data (v .gitignore, aktualizace na ně nesahá)

`history.db` (SQLite, zakázky, částky v herní měně: € / $), `session.json` (relace),
`config.json` (nastavení), `job_progress.json` (rozjeté hodnocení stylu, přežije restart hry), `dash.log`, `backup/`.

## Důležitá rozhodnutí

- Částky se ukládají v herní měně a přepočítávají až při zobrazení. Výchozí kurz CZK = 24,4945 (kurz hry).
- Tolerance rychlosti: statistiky i hodnocení počítají až od **+6 km/h** (`SPEED_TOL_KMH = 5`).
  Palubka: +1 až +5 oranžová, od +6 červená s pulzem značky (`SPEED_WARN_KMH = 5` v HTML).
- Hodnocení stylu: brzdění > 4,5 m/s² a zatáčky > 3,5 m/s² trvající 0,5 s, počítané na 100 km
  (8 bodů), nárazy podle velikosti poškození (`hit_penalty`, 1–15 bodů), nad limitem 1,5 bodu za %.
- Reálné časy se přepočítávají „silničním" měřítkem (nejvyšší viděné), ne městským 1:3.
- Externí zakázky: hra termín neposílá (`timeAbsDelivery` = max hodnota), UI ukáže „hra ho neposílá".
- Telemetrie **neposílá**: zemi, počasí, waypointy, benzinky, zůstatek účtu, kurýrní zakázky Road Tripu.
  Nenavrhovat obcházení čtením paměti hry.
- Bez hry je přes dashboard překryv „Čekám na hru" (cs + en).

## Vydání nové verze

1. Zvednout `VERSION` v `dash.py` (SemVer: nová funkce = minor, oprava = patch).
2. Commit + push.
3. GitHub Release s tagem `vX.Y.Z`, **do názvu releasu napsat, co je nového** (ukáže se uživatelům v liště).
   Tag musí sedět s `VERSION`, jinak updater instalaci odmítne.

Nové soubory, které mají chodit uživatelům aktualizací, přidat do `UPDATE_FILES`.

## Testování

- `python dash.py --demo` a otevřít http://127.0.0.1:8088.
- Po úpravě HTML vždy zkontrolovat i menší rozlišení (1280×720, 1024×768), aby sloupce nepřetékaly.
