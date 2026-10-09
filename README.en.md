# Palubka – dashboard for ETS2 and ATS

[Česky](README.md)

A second-monitor dashboard for Euro Truck Simulator 2 and American Truck Simulator.
It runs only on your computer and sends nothing out.

<img width="3840" height="1080" alt="01" src="https://github.com/user-attachments/assets/1c187ae3-80c8-4027-9fb2-fd0ed215b015" />
<img width="1907" height="1073" alt="04" src="https://github.com/user-attachments/assets/ebd5d9c9-ef22-402b-9205-e3feb2ab6d1a" />

## Installation

1. Download and install [Python](https://www.python.org/downloads/) (version 3.9 or newer).
   - During installation, tick **"Add python.exe to PATH"**.
2. Copy `scs-telemetry.dll` from the `Install files` folder into the game's `plugins` folder.
   The `plugins` folder doesn't exist by default, you have to create it.
   - ETS2: `<your_path>\steamapps\common\Euro Truck Simulator 2\bin\win_x64\plugins\`
   - ATS: `<your_path>\steamapps\common\American Truck Simulator\bin\win_x64\plugins\`
3. Start the dashboard with `dashboard-start.bat`.
4. Start the game. Confirm the SDK message when the game starts. Everything else syncs on its own.

Full screen: **F** key. Job history: **H** key. Language, currency and units: gear icon.

## Tip: start automatically with the game

1. In Steam, right-click the game → **Properties**.
2. Paste this into **Launch Options**:

   ```
   "<path to your dashboard>\game-start.bat" %command%
   ```

The dashboard then starts with the game and closes when you quit it.

<img width="841" height="598" alt="image" src="https://github.com/user-attachments/assets/d542820c-781f-4297-b610-fcc0cccf5df3" />

## Updates

On startup the dashboard checks here on GitHub for a new version. If there is one, it shows
a bar, and clicking **Update** updates it. Your data (history, statistics, settings) is kept.
You can turn the check off in Settings (gear icon).

## License

The dashboard is licensed under [GPL-3.0](LICENSE).

It uses [scs-sdk-plugin](https://github.com/RenCloud/scs-sdk-plugin) (RenCloud) and is based on
[TruckSim-Telemetry](https://github.com/kniffen/TruckSim-Telemetry) (Kniffen), both under the MIT license.
Details in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
