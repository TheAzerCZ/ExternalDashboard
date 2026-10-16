# Palubka – dashboard for ETS2 and ATS

[Česky](README.md)

A second-monitor dashboard for Euro Truck Simulator 2 and American Truck Simulator.
It runs only on your computer and sends nothing out.

<img width="3840" height="1080" alt="01" src="https://github.com/user-attachments/assets/1c187ae3-80c8-4027-9fb2-fd0ed215b015" />
<img width="1907" height="1073" alt="04" src="https://github.com/user-attachments/assets/ebd5d9c9-ef22-402b-9205-e3feb2ab6d1a" />

## Features
 
- **Destination sign**: remaining distance, real-time ETA and arrival, in-game driving time and arrival, route progress.
- **Driving**: speed with the limit (orange up to +5 km/h, red with a pulse above that), cruise control, gear and RPM, warning lights as icons, blinkers, diesel, AdBlue, range and fuel consumption.
- **Rest & plan**: time to mandatory rest (orange on the warning, red when it's due), whether you make it without sleeping and how much time you have left, whether your fuel lasts (how much is missing and where it runs out), in-game and real time.
- **Job**: cargo, pay and pay per km, delivery deadline, time buffer, cargo damage.
- **Vehicle**: truck and trailer wear, temperatures and pressures, collision alerts.
- **Session**: distance, time at the wheel, net profit, fines, tolls, ferries, fuel used, average speed, time over the limit and an event log. Resets automatically when the game starts.
- **Delivery summary**: revenue, XP, distance and a driving style score (braking, cornering, collisions, speeding).
- **Job history**: earnings per day chart and a job table, separate for ETS2 and ATS.
- **RPM LEDs on the wheel** for Logitech G29 / G27.
- **Floating video**: YouTube (video, playlist, live stream) or Twitch (channel, past broadcast) in a window you can move and resize. YouTube pauses on its own when the game is paused.
- **Settings**: Czech / English, currency, exchange rate and units (km / miles), separate for ETS2 and ATS.
- **Automatic updates** from GitHub with one click.

## Installation

1. Download and install [Python](https://www.python.org/downloads/) (version 3.9 or newer).
   - During installation, tick **"Add python.exe to PATH"**.
2. Copy `scs-telemetry.dll` from the `Install files` folder into the game's `plugins` folder.
   The `plugins` folder doesn't exist by default, you have to create it.
   - ETS2: `<your_path>\steamapps\common\Euro Truck Simulator 2\bin\win_x64\plugins\`
   - ATS: `<your_path>\steamapps\common\American Truck Simulator\bin\win_x64\plugins\`
3. Start the dashboard with `dashboard-start.bat`.
4. Start the game. Confirm the SDK message when the game starts. Everything else syncs on its own.

Full screen: **F** key. Job history: **H** key. Video: **V** key. Language, currency and units: gear icon.

## Tip: start automatically with the game

1. In Steam, right-click the game → **Properties**.
2. Paste this into **Launch Options**:

   ```
   "<path to your dashboard>\game-start.bat" %command%
   ```

<img width="841" height="598" alt="image" src="https://github.com/user-attachments/assets/d542820c-781f-4297-b610-fcc0cccf5df3" />

The dashboard then starts with the game and closes when you quit it.

## Tip: RPM LEDs on the wheel (Logitech G29 / G27)
 
The LEDs on your wheel light up with engine RPM and blink above the red line.
 
1. In a command prompt, run once: `pip install hidapi`
2. In the dashboard, open Settings (gear icon) and turn on **RPM LEDs on the wheel**.
3. Below the option you'll see "Connected: Logitech G29". If not, check that the wheel is plugged in.

## Updates

On startup the dashboard checks here on GitHub for a new version. If there is one, it shows
a bar, and clicking **Update** updates it. Your data (history, statistics, settings) is kept.
You can turn the check off in Settings (gear icon).

## License

The dashboard is licensed under [GPL-3.0](LICENSE).

It uses [scs-sdk-plugin](https://github.com/RenCloud/scs-sdk-plugin) (RenCloud) and is based on
[TruckSim-Telemetry](https://github.com/kniffen/TruckSim-Telemetry) (Kniffen), both under the MIT license.
Details in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
