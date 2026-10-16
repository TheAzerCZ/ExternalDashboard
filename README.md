# Palubka – dashboard pro ETS2 a ATS

[English](README.en.md)

Dashboard na druhý monitor pro Euro Truck Simulator 2 a American Truck Simulator.
Běží jen u tebe na počítači, nic neposílá ven.

<img width="3840" height="1080" alt="02" src="https://github.com/user-attachments/assets/c2fdebc3-228b-4928-9983-cf1c34b46930" />
<img width="1917" height="1080" alt="03" src="https://github.com/user-attachments/assets/5319c144-3cd1-4b48-a80a-48184a4f906e" />

## Co umí
 
- **Cedule s cílem**: zbývající vzdálenost, reálné ETA a čas příjezdu, herní čas jízdy a herní příjezd, průběh trasy.
- **Jízda**: rychlost s limitem (do +5 km/h oranžová, nad to červená s pulzem), tempomat, rychlostní stupeň a otáčky, kontrolky jako ikony, blinkry, nafta, AdBlue, dojezd a spotřeba.
- **Odpočinek a plán**: čas do povinné pauzy (oranžově při upozornění, červeně po vypršení), jestli dojedeš bez spánku a s jakou zálohou, jestli stačí nafta (kolik chybí a kde dojde), herní a reálný čas.
- **Zakázka**: náklad, výplata a cena za km, termín doručení, rezerva, poškození nákladu.
- **Vůz**: opotřebení tahače i návěsu, teploty a tlaky, upozornění na nárazy.
- **Relace**: najeté km, čas za volantem, čistý zisk, pokuty, mýtné, trajekty, spotřeba, průměrná rychlost, čas nad limitem a log událostí. Při spuštění hry se sama vynuluje.
- **Souhrn po doručení**: výdělek, XP, najeté km a hodnocení stylu jízdy (brzdění, zatáčky, nárazy, rychlost).
- **Historie zakázek**: graf výdělku po dnech a tabulka zakázek, zvlášť pro ETS2 a ATS.
- **RPM diody na volantu** Logitech G29 / G27.
- **Plovoucí video**: YouTube (video, playlist, živý přenos) nebo Twitch (kanál, záznam) v okně, které si posuneš a zvětšíš. YouTube se při pauze hry sám zastaví.
- **Nastavení**: čeština / angličtina, měna a kurz a jednotky (km / míle) zvlášť pro ETS2 a ATS.
- **Automatické aktualizace** z GitHubu jedním kliknutím.

## Instalace

1. Stáhni a nainstaluj [Python](https://www.python.org/downloads/) (verze 3.9 nebo novější).
   - Při instalaci zaškrtni **„Add python.exe to PATH"**.
2. Zkopíruj `scs-telemetry.dll` ze složky `Install files` do složky `plugins` ve hře.
   Složka `plugins` ve výchozím stavu neexistuje, musíš ji vytvořit.
   - ETS2: `<tvoje_cesta>\steamapps\common\Euro Truck Simulator 2\bin\win_x64\plugins\`
   - ATS: `<tvoje_cesta>\steamapps\common\American Truck Simulator\bin\win_x64\plugins\`
3. Spusť dashboard přes `dashboard-start.bat`.
4. Zapni hru. Při startu hry potvrď hlášku o SDK. Pak už se vše synchronizuje samo.

Celá obrazovka: klávesa **F**. Historie zakázek: klávesa **H**. Video: klávesa **V**. Jazyk, měna a jednotky: ozubené kolo.

## Tip: automatické spouštění se hrou

1. Ve Steamu klikni pravým na hru → **Vlastnosti**.
2. Do **Parametrů spuštění** (Launch Options) vlož:

   ```
   "<cesta, kde máš dashboard>\game-start.bat" %command%
   ```

Dashboard se pak zapne se hrou a po jejím zavření se sám vypne.

<img width="841" height="609" alt="image" src="https://github.com/user-attachments/assets/5d7af9cf-3a29-4c98-b4a2-e2bb0aa61033" />

## Tip: RPM diody na volantu (Logitech G29 / G27)
 
Diody na volantu se rozsvěcují podle otáček motoru, nad červenou hranicí blikají.
 
1. V příkazovém řádku jednou spusť: `pip install hidapi`
2. V dashboardu otevři Nastavení (ozubené kolo) a zapni **RPM diody na volantu**.
3. Pod volbou uvidíš „Připojeno: Logitech G29". Když ne, zkontroluj, že je volant zapojený.

## Aktualizace

Dashboard se při startu podívá sem na GitHub, jestli je nová verze. Když ano, ukáže lištu
a po kliknutí na **Aktualizovat** se sám aktualizuje. Tvoje data (historie, statistiky,
nastavení) zůstanou. Kontrolu jde vypnout v Nastavení (ozubené kolo).

## Licence

Dashboard je pod licencí [GPL-3.0](LICENSE).

Používá [scs-sdk-plugin](https://github.com/RenCloud/scs-sdk-plugin) (RenCloud) a vychází
z [TruckSim-Telemetry](https://github.com/kniffen/TruckSim-Telemetry) (Kniffen), oba pod licencí MIT.
Podrobnosti v [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
