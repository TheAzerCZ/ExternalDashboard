# Palubka – dashboard pro ETS2 a ATS

[English](README.en.md)

Dashboard na druhý monitor pro Euro Truck Simulator 2 a American Truck Simulator.
Běží jen u tebe na počítači, nic neposílá ven.

<img width="3840" height="1080" alt="02" src="https://github.com/user-attachments/assets/c2fdebc3-228b-4928-9983-cf1c34b46930" />
<img width="1917" height="1080" alt="03" src="https://github.com/user-attachments/assets/5319c144-3cd1-4b48-a80a-48184a4f906e" />

## Instalace

1. Stáhni a nainstaluj [Python](https://www.python.org/downloads/) (verze 3.9 nebo novější).
   - Při instalaci zaškrtni **„Add python.exe to PATH"**.
2. Zkopíruj `scs-telemetry.dll` ze složky `Install files` do složky `plugins` ve hře.
   Složka `plugins` ve výchozím stavu neexistuje, musíš ji vytvořit.
   - ETS2: `<tvoje_cesta>\steamapps\common\Euro Truck Simulator 2\bin\win_x64\plugins\`
   - ATS: `<tvoje_cesta>\steamapps\common\American Truck Simulator\bin\win_x64\plugins\`
3. Spusť dashboard přes `dashboard-start.bat`.
4. Zapni hru. Při startu hry potvrď hlášku o SDK. Pak už se vše synchronizuje samo.

Celá obrazovka: klávesa **F**. Historie zakázek: klávesa **H**. Jazyk, měna a jednotky: ozubené kolo.

## Tip: automatické spouštění se hrou

1. Ve Steamu klikni pravým na hru → **Vlastnosti**.
2. Do **Parametrů spuštění** (Launch Options) vlož:

   ```
   "<cesta, kde máš dashboard>\game-start.bat" %command%
   ```

Dashboard se pak zapne se hrou a po jejím zavření se sám vypne.

## Aktualizace

Dashboard se při startu podívá sem na GitHub, jestli je nová verze. Když ano, ukáže lištu
a po kliknutí na **Aktualizovat** se sám aktualizuje. Tvoje data (historie, statistiky,
nastavení) zůstanou. Kontrolu jde vypnout v Nastavení (ozubené kolo).

## Licence

Dashboard je pod licencí [GPL-3.0](LICENSE).

Používá [scs-sdk-plugin](https://github.com/RenCloud/scs-sdk-plugin) (RenCloud) a vychází
z [TruckSim-Telemetry](https://github.com/kniffen/TruckSim-Telemetry) (Kniffen), oba pod licencí MIT.
Podrobnosti v [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
