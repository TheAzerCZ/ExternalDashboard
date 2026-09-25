"""
ETS2 / ATS lokální dashboard
============================
Čte telemetrii ze sdílené paměti pluginu RenCloud/scs-sdk-plugin ("Local\\SCSTelemetry")
a servíruje fullscreen dashboard na http://127.0.0.1:8088.

Jen standardní knihovna Pythonu (3.9+), žádné pip balíčky, žádná spojení ven.

Spuštění:
    python dash.py              # jen localhost
    python dash.py --demo       # simulovaná data bez hry (na odzkoušení UI)
    python dash.py --lan        # zpřístupní i v LAN (tablet/mobil) - volitelné
    python dash.py --rate 24.5  # vlastní kurz EUR -> CZK (výchozí je herní 24,4945)
"""

import argparse
import ctypes
import json
import math
import os
import random
import sqlite3
import struct
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
STATS_FILE = os.path.join(HERE, "session.json")
HISTORY_DB = os.path.join(HERE, "history.db")
DRIVE_AFTER_SLEEP_MIN = 11 * 60  # po vyspání má řidič v ETS2 11 h herního času jízdy
MAP_NAME = "Local\\SCSTelemetry"
READ_SIZE = 8192  # hlavní struktura + 1. návěs (layout pluginu v1.12)

WHEEL_COUNT, GEAR_COUNT = 16, 32
FWD_GEARS, REV_GEARS = 24, 8
STR, SHIFTER_STR, MARKET_STR, OFFENCE_STR = 64, 16, 32, 32


# --------------------------------------------------------------------------
#  Parsování binárního layoutu (port z kniffen/TruckSim-Telemetry, MIT)
# --------------------------------------------------------------------------
class Reader:
    def __init__(self, buf):
        self.b, self.c = buf, 0

    def at(self, pos):
        self.c = pos

    def skip(self, n):
        self.c += n

    def _u(self, fmt, size):
        v = struct.unpack_from(fmt, self.b, self.c)[0]
        self.c += size
        return v

    def bool(self): return self._u("<B", 1) != 0
    def uint(self): return self._u("<I", 4)
    def int(self): return self._u("<i", 4)
    def float(self): return self._u("<f", 4)
    def double(self): return self._u("<d", 8)
    def ull(self): return self._u("<Q", 8)
    def ll(self): return self._u("<q", 8)

    def str(self, size):
        raw = self.b[self.c:self.c + size]
        self.c += size
        return raw.split(b"\0", 1)[0].decode("utf-8", "replace")


def parse(buf):
    r, d = Reader(buf), {}
    # zóna 1
    r.at(0)
    d["sdkActive"] = r.bool(); r.skip(3)
    d["paused"] = r.bool(); r.skip(3)
    d["time"] = r.ull()
    # zóna 2
    r.at(40)
    for k in ("pluginRev", "verMajor", "verMinor", "game", "telVerMajor", "telVerMinor",
              "timeAbs", "gears", "gearsReverse", "retarderStepCount", "truckWheelCount",
              "selectorCount", "timeAbsDelivery", "maxTrailerCount", "unitCount",
              "plannedDistanceKm", "shifterSlot", "retarderBrake", "lightsAuxFront", "lightsAuxRoof"):
        d[k] = r.uint()
    r.skip(4 * (WHEEL_COUNT + GEAR_COUNT + GEAR_COUNT))
    d["jobDeliveredDeliveryTime"] = r.uint()
    d["jobStartingTime"] = r.uint()
    d["jobFinishedTime"] = r.uint()
    # zóna 3
    r.at(500)
    d["restStop"] = r.int()
    d["gear"] = r.int()
    d["gearDashboard"] = r.int()
    r.skip(4 * GEAR_COUNT)
    d["jobDeliveredEarnedXp"] = r.int()
    # zóna 4
    r.at(700)
    for k in ("scale", "fuelCapacity", "fuelWarningFactor", "adblueCapacity", "adblueWarningFactor",
              "airPressureWarningFactor", "airPressureEmergencyFactor", "oilPressureWarningFactor",
              "waterTemperatureWarningFactor", "batteryVoltageWarningFactor", "engineRpmMax",
              "gearDifferential", "cargoMass"):
        d[k] = r.float()
    r.skip(4 * (WHEEL_COUNT + FWD_GEARS + REV_GEARS))
    for k in ("unitMass", "speed", "engineRpm", "userSteer", "userThrottle", "userBrake", "userClutch",
              "gameSteer", "gameThrottle", "gameBrake", "gameClutch", "cruiseControlSpeed",
              "airPressure", "brakeTemperature", "fuel", "fuelAvgConsumption", "fuelRange", "adblue",
              "oilPressure", "oilTemperature", "waterTemperature", "batteryVoltage", "lightsDashboard",
              "wearEngine", "wearTransmission", "wearCabin", "wearChassis", "wearWheels",
              "truckOdometer", "routeDistance", "routeTime", "speedLimit"):
        d[k] = r.float()
    r.skip(4 * WHEEL_COUNT * 6)
    for k in ("jobDeliveredCargoDamage", "jobDeliveredDistanceKm", "refuelAmount", "cargoDamage"):
        d[k] = r.float()
    # zóna 5
    r.at(1500)
    r.skip(4 * WHEEL_COUNT)
    for k in ("isCargoLoaded", "specialJob", "parkBrake", "motorBrake", "airPressureWarning",
              "airPressureEmergency", "fuelWarning", "adblueWarning", "oilPressureWarning",
              "waterTemperatureWarning", "batteryVoltageWarning", "electricEnabled", "engineEnabled",
              "wipers", "blinkerLeftActive", "blinkerRightActive", "blinkerLeftOn", "blinkerRightOn",
              "lightsParking", "lightsBeamLow", "lightsBeamHigh", "lightsBeacon", "lightsBrake",
              "lightsReverse", "lightsHazard", "cruiseControl"):
        d[k] = r.bool()
    r.skip(WHEEL_COUNT + 2)
    for k in ("differentialLock", "liftAxle", "liftAxleIndicator", "trailerLiftAxle",
              "trailerLiftAxleIndicator", "jobDeliveredAutoparkUsed", "jobDeliveredAutoloadUsed"):
        d[k] = r.bool()
    # zóna 9 - řetězce
    r.at(2300)
    for k in ("truckBrandId", "truckBrand", "truckId", "truckName", "cargoId", "cargo",
              "cityDstId", "cityDst", "compDstId", "compDst", "citySrcId", "citySrc",
              "compSrcId", "compSrc"):
        d[k] = r.str(STR)
    d["shifterType"] = r.str(SHIFTER_STR)
    for k in ("truckLicensePlate", "truckLicensePlateCountryId", "truckLicensePlateCountry"):
        d[k] = r.str(STR)
    d["jobMarket"] = r.str(MARKET_STR)
    d["fineOffence"] = r.str(OFFENCE_STR)
    for k in ("ferrySourceName", "ferryTargetName", "ferrySourceId", "ferryTargetId",
              "trainSourceName", "trainTargetName", "trainSourceId", "trainTargetId"):
        d[k] = r.str(STR)
    # zóna 10/11
    r.at(4000)
    d["jobIncome"] = r.ull()
    r.at(4200)
    for k in ("jobCancelledPenalty", "jobDeliveredRevenue", "fineAmount", "tollgatePayAmount",
              "ferryPayAmount", "trainPayAmount"):
        d[k] = r.ll()
    # zóna 12 - příznaky událostí (plugin je při události přepíná XORem)
    r.at(4300)
    for k in ("onJob", "jobFinished", "jobCancelled", "jobDelivered", "fined", "tollgate",
              "ferry", "train", "refuel", "refuelPayed"):
        d[k] = r.bool()
    # 1. návěs
    t = 6000
    r.at(t + 80)
    d["trailerAttached"] = r.bool()
    r.at(t + 152)
    for k in ("trailerCargoDamage", "trailerWearChassis", "trailerWearWheels", "trailerWearBody"):
        d[k] = r.float()
    r.at(t + 920 + 4 * STR)
    d["trailerBrand"] = r.str(STR)
    d["trailerName"] = r.str(STR)
    return d


# --------------------------------------------------------------------------
#  Zdroje dat
# --------------------------------------------------------------------------
class SharedMemorySource:
    """Jen OTEVÍRÁ existující mapování (nikdy ho nevytváří), read-only."""

    def __init__(self):
        if sys.platform != "win32":
            raise RuntimeError("Sdílená paměť SCS je dostupná jen na Windows. Použij --demo.")
        from ctypes import wintypes
        self.k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.k32.OpenFileMappingW.restype = wintypes.HANDLE
        self.k32.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
        self.k32.MapViewOfFile.restype = ctypes.c_void_p
        self.k32.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                           wintypes.DWORD, ctypes.c_size_t]
        self.k32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        self.k32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = self.view = None

    def _open(self):
        FILE_MAP_READ = 0x0004
        h = self.k32.OpenFileMappingW(FILE_MAP_READ, False, MAP_NAME)
        if not h:
            return False
        v = self.k32.MapViewOfFile(h, FILE_MAP_READ, 0, 0, READ_SIZE)
        if not v:
            self.k32.CloseHandle(h)
            return False
        self.handle, self.view = h, v
        return True

    def close(self):
        if self.view:
            self.k32.UnmapViewOfFile(self.view)
        if self.handle:
            self.k32.CloseHandle(self.handle)
        self.handle = self.view = None

    def read(self):
        if not self.view and not self._open():
            return None
        d = parse(ctypes.string_at(self.view, READ_SIZE))
        if not d["sdkActive"]:
            # hra se ukončila -> pustíme handle, aby se mapování mohlo uvolnit
            self.close()
            return None
        return d


class DemoSource:
    """Simulovaná jízda Dortmund -> Stockholm, ať jde UI vyzkoušet bez hry."""

    def __init__(self):
        self.t0 = time.time()
        self.odo = 184_512.0
        self.fuel = 790.0
        self.dist = 1_129_500.0
        self.flags = dict(fined=False, tollgate=False, ferry=False, train=False,
                          jobDelivered=False, jobCancelled=False)
        self.next_event = time.time() + 6
        self.last = time.time()
        self.cab = 0.10
        self.delivered_at = time.time() + 25

    def read(self):
        now = time.time()
        dt, self.last = now - self.last, now
        el = now - self.t0
        speed = 72 + 14 * math.sin(el / 9) + 4 * math.sin(el / 2.3)
        ms = speed / 3.6
        self.odo += ms * dt / 1000
        self.dist = max(0.0, self.dist - ms * dt * 19)
        self.fuel -= 0.395 * ms * dt / 1000 * 19
        if now > self.next_event:
            self.next_event = now + random.uniform(8, 16)
            kind = random.choice(["tollgate", "tollgate", "fined", "ferry", "damage"])
            if kind == "damage":
                self.cab += 0.012
            else:
                self.flags[kind] = not self.flags[kind]
        if self.delivered_at and now > self.delivered_at:
            self.delivered_at = None
            self.flags["jobDelivered"] = not self.flags["jobDelivered"]
        d = {
            "sdkActive": True, "paused": False, "game": 1, "scale": 19.0, "time": int(el * 1e6),
            "timeAbs": 6 * 1440 + 12 * 60 + 15 + int(el * 19 / 60),
            "timeAbsDelivery": 6 * 1440 + 12 * 60 + 15 + 40 * 60 + 54,
            "restStop": max(0, 272 - int(el * 19 / 60)),
            "gearDashboard": 12, "gears": 12, "gearsReverse": 4, "shifterType": "arcade",
            "retarderBrake": 0, "retarderStepCount": 4,
            "speed": ms, "engineRpm": 1150 + 200 * math.sin(el / 9), "engineRpmMax": 2500,
            "cruiseControl": True, "cruiseControlSpeed": 80 / 3.6, "speedLimit": 80 / 3.6,
            "fuel": self.fuel, "fuelCapacity": 1400, "fuelAvgConsumption": 0.395,
            "fuelRange": self.fuel / 0.395 * 0.42, "adblue": 61, "adblueCapacity": 80,
            "airPressure": 124, "brakeTemperature": 48, "oilPressure": 52, "oilTemperature": 91,
            "waterTemperature": 84, "batteryVoltage": 26.1,
            "fuelWarning": False, "adblueWarning": False, "airPressureWarning": False,
            "oilPressureWarning": False, "waterTemperatureWarning": False, "batteryVoltageWarning": False,
            "wearEngine": 0.0, "wearTransmission": 0.03, "wearCabin": self.cab, "wearChassis": 0.13,
            "wearWheels": 0.48, "truckOdometer": self.odo,
            "routeDistance": self.dist, "routeTime": self.dist / 19.5,
            "parkBrake": False, "engineEnabled": True, "electricEnabled": True,
            "lightsBeamLow": True, "lightsBeamHigh": False, "lightsBeacon": False, "lightsHazard": False,
            "wipers": True, "blinkerLeftOn": int(el * 2) % 2 == 0 and int(el / 10) % 3 == 0,
            "blinkerRightOn": False, "differentialLock": False, "liftAxle": False, "motorBrake": False,
            "truckBrand": "Scania", "truckName": "S", "truckLicensePlate": "4T2 0815",
            "onJob": True, "specialJob": False, "isCargoLoaded": True,
            "cargo": "Venkovní dlažba", "cargoMass": 20000, "cargoDamage": 0.012,
            "citySrc": "Dortmund", "cityDst": "Stockholm", "compSrc": "Posped", "compDst": "Stokes",
            "jobIncome": 44822, "plannedDistanceKm": 1318, "jobMarket": "freight_market",
            "trailerAttached": True, "trailerBrand": "Krone", "trailerName": "Cool Liner",
            "trailerWearChassis": 0.04, "trailerWearWheels": 0.06, "trailerWearBody": 0.02,
            "trailerCargoDamage": 0.012,
            "fineAmount": random.choice([150, 300, 720]), "tollgatePayAmount": random.choice([12, 18, 31]),
            "ferryPayAmount": 460, "ferrySourceName": "Rostock", "ferryTargetName": "Trelleborg",
            "trainPayAmount": 0, "trainSourceName": "", "trainTargetName": "",
            "jobCancelledPenalty": 0, "jobDeliveredRevenue": 44822, "jobDeliveredEarnedXp": 1873,
            "jobDeliveredDistanceKm": 1322.4, "jobDeliveredCargoDamage": 0.012, "jobDeliveredAutoparkUsed": False,
            "fineOffence": random.choice(["speeding_camera", "red_signal", "no_lights"]),
            **self.flags,
        }
        return d


# --------------------------------------------------------------------------
#  Statistiky relace + události
# --------------------------------------------------------------------------
OFFENCES = {
    "crash": "Nehoda", "avoid_sleeping": "Jízda bez odpočinku", "wrong_way": "Jízda v protisměru",
    "speeding_camera": "Radar", "speeding": "Překročení rychlosti", "no_lights": "Jízda bez světel",
    "red_signal": "Jízda na červenou", "avoid_weighing": "Vyhnutí se vážení",
    "illegal_trailer": "Nepovolený návěs", "avoid_inspection": "Vyhnutí se kontrole",
    "illegal_border_crossing": "Nelegální přejezd hranice", "hard_shoulder_violation": "Jízda po krajnici",
    "damaged_vehicle_usage": "Poškozené vozidlo", "generic": "Pokuta",
}


def fresh_stats():
    return {"since": time.time(), "km": 0.0, "fuel_l": 0.0, "drive_s": 0.0, "speeding_s": 0.0,
            "max_kmh": 0.0, "speed_int": 0.0, "fines": [], "tolls_n": 0, "tolls_sum": 0, "transport": [],
            "jobs": [], "log": [], "last_time": 0, "game_over": False}


class Processor:
    FLAGS = ("fined", "tollgate", "ferry", "train", "jobDelivered", "jobCancelled")

    def __init__(self, source, eur_czk, usd_czk=21.0, auto_reset=True):
        self.src, self.rate, self.usd, self.auto_reset = source, eur_czk, usd_czk, auto_reset
        self.lock = threading.Lock()
        self.game_exited = threading.Event()
        self.stats = self._load()
        self.prev = None
        self.pending = []  # události se zpracují až v dalším ticku (plugin dopisuje atributy)
        self.last_job = {}
        self.odo_anchor = self.fuel_anchor = None
        self.dmg_acc, self.dmg_t, self.last_damage = {}, 0.0, 0.0
        self.delivery = None
        self.view = {"connected": False}
        self.db = sqlite3.connect(HISTORY_DB, check_same_thread=False)
        self.db.execute("""CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY, ts REAL, game TEXT, ok INTEGER, src TEXT, dst TEXT,
            comp_src TEXT, comp_dst TEXT, cargo TEXT, mass REAL, planned_km REAL, driven_km REAL,
            revenue REAL, xp INTEGER, damage REAL, market TEXT)""")
        self.db.commit()
        self.last_tick = time.time()
        self.last_save = time.time()

    def _load(self):
        try:
            with open(STATS_FILE, encoding="utf-8") as f:
                s = json.load(f)
            base = fresh_stats(); base.update(s)
            return base
        except (OSError, ValueError):
            return fresh_stats()

    def save(self):
        try:
            tmp = STATS_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, ensure_ascii=False)
            os.replace(tmp, STATS_FILE)
        except OSError:
            pass

    def reset(self):
        with self.lock:
            self.stats = fresh_stats()
            self.save()

    def _log(self, kind, text, amount=None):
        self.stats["log"].insert(0, {"t": time.time(), "kind": kind, "text": text, "amount": amount})
        del self.stats["log"][40:]

    def _fire(self, flag, d):
        s = self.stats
        if flag == "fined":
            name = OFFENCES.get(d["fineOffence"], d["fineOffence"] or "Pokuta")
            s["fines"].append({"what": name, "amount": d["fineAmount"]})
            self._log("fine", name, d["fineAmount"])
        elif flag == "tollgate":
            s["tolls_n"] += 1
            s["tolls_sum"] += d["tollgatePayAmount"]
            self._log("toll", "Mýtná brána", d["tollgatePayAmount"])
        elif flag in ("ferry", "train"):
            a = d[f"{flag}PayAmount"]
            text = f'{"Trajekt" if flag == "ferry" else "Vlak"} {d[flag + "SourceName"]} – {d[flag + "TargetName"]}'
            s["transport"].append({"kind": flag, "text": text, "amount": a})
            self._log(flag, text, a)
        elif flag == "jobDelivered":
            j = self.last_job
            job = {"ok": True, "from": j.get("citySrc", "?"), "to": j.get("cityDst", "?"),
                   "cargo": j.get("cargo", ""), "revenue": d["jobDeliveredRevenue"],
                   "xp": d["jobDeliveredEarnedXp"], "km": round(d["jobDeliveredDistanceKm"]),
                   "damage": d["jobDeliveredCargoDamage"], "t": time.time()}
            s["jobs"].insert(0, job)
            self._log("job", f'Doručeno: {job["from"]} → {job["to"]}', job["revenue"])
            self._store(d, j, True, d["jobDeliveredRevenue"])
            self.delivery = {**job, "t": time.time(), "plannedKm": j.get("plannedDistanceKm", 0),
                             "autopark": d["jobDeliveredAutoparkUsed"]}
        elif flag == "jobCancelled":
            j = self.last_job
            s["jobs"].insert(0, {"ok": False, "from": j.get("citySrc", "?"), "to": j.get("cityDst", "?"),
                                 "cargo": j.get("cargo", ""), "revenue": -d["jobCancelledPenalty"],
                                 "t": time.time()})
            self._log("cancel", "Zakázka zrušena", d["jobCancelledPenalty"])
            self._store(d, j, False, -d["jobCancelledPenalty"])

    def _store(self, d, j, ok, revenue):
        try:
            self.db.execute(
                "INSERT INTO jobs (ts, game, ok, src, dst, comp_src, comp_dst, cargo, mass, planned_km,"
                " driven_km, revenue, xp, damage, market) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (time.time(), {1: "ETS2", 2: "ATS"}.get(d["game"], "?"), int(ok), j.get("citySrc", "?"),
                 j.get("cityDst", "?"), j.get("compSrc", ""), j.get("compDst", ""), j.get("cargo", ""),
                 j.get("cargoMass", 0), j.get("plannedDistanceKm", 0),
                 d["jobDeliveredDistanceKm"] if ok else 0, revenue,
                 d["jobDeliveredEarnedXp"] if ok else 0, d["jobDeliveredCargoDamage"] if ok else 0,
                 j.get("jobMarket", "")))
            self.db.commit()
        except sqlite3.Error as e:
            print("Nepodařilo se uložit zakázku do historie:", e)

    def history(self):
        with self.lock:
            cur = self.db.cursor()
            jobs = [dict(zip([c[0] for c in cur.description], r)) for r in
                    cur.execute("SELECT * FROM jobs ORDER BY ts DESC LIMIT 25").fetchall()]
            days = [dict(zip(("day", "n", "revenue", "km"), r)) for r in cur.execute(
                "SELECT date(ts, 'unixepoch', 'localtime') d, COUNT(*), SUM(revenue),"
                " SUM(CASE WHEN driven_km > 0 THEN driven_km ELSE planned_km END)"
                " FROM jobs GROUP BY d ORDER BY d DESC LIMIT 14").fetchall()]
            t = cur.execute("SELECT COUNT(*), SUM(ok), SUM(revenue), SUM(CASE WHEN ok THEN"
                            " (CASE WHEN driven_km > 0 THEN driven_km ELSE planned_km END) END),"
                            " SUM(xp), MIN(ts) FROM jobs").fetchone()
            best = cur.execute("SELECT src, dst, revenue, planned_km FROM jobs WHERE ok AND planned_km > 0"
                               " ORDER BY revenue / planned_km DESC LIMIT 1").fetchone()
            return json.dumps({
                "rate": self.rate, "jobs": jobs, "days": days[::-1],
                "totals": {"n": t[0] or 0, "ok": t[1] or 0, "revenue": t[2] or 0, "km": t[3] or 0,
                           "xp": t[4] or 0, "since": t[5]},
                "best": dict(zip(("src", "dst", "revenue", "km"), best)) if best else None,
            }, ensure_ascii=False)

    def tick(self):
        now = time.time()
        dt, self.last_tick = now - self.last_tick, now
        d = self.src.read()
        with self.lock:
            if d is None:
                if self.prev is not None:
                    # hra se ukončila -> příští připojení je nová herní relace
                    self.stats["game_over"] = True
                    self.save()
                    self.game_exited.set()
                self.prev = None
                self.road_scale = 0
                self.odo_anchor = self.fuel_anchor = None
                self.view = {"connected": False, "stats": self._stats_view(None)}
                return
            if self.prev is None:
                # připojení ke hře: nové spuštění hry poznáme tak, že jsme viděli její konec,
                # nebo že čítač času pluginu (od startu hry) je menší než naposledy uložený
                t = d.get("time", 0)
                if self.auto_reset and (self.stats.get("game_over") or t < self.stats.get("last_time", 0)):
                    self.stats = fresh_stats()
                    self._log("info", "Hra spuštěna, nová relace")
                self.stats["game_over"] = False
                self.prev = d  # po (re)startu hry nevyhodnocujeme přepnuté příznaky
            self.stats["last_time"] = d.get("time", 0)
            for flag in self.pending:
                self._fire(flag, d)
            self.pending = [f for f in self.FLAGS if d.get(f) != self.prev.get(f)]
            if d["onJob"] and d["cityDst"]:
                self.last_job = {k: d[k] for k in ("citySrc", "cityDst", "cargo", "compSrc", "compDst",
                                                   "cargoMass", "plannedDistanceKm", "jobMarket")}
            if not d["paused"]:
                self._check_damage(d, now)

            # průběžné statistiky
            if not d["paused"]:
                # Počítáme proti "kotvě" s malou tolerancí, aby drobné kmitání
                # float hodnot (odometr, nádrž) nenafukovalo součty.
                odo, fuel = d["truckOdometer"], d["fuel"]
                if self.odo_anchor is None or abs(odo - self.odo_anchor) > 5:
                    self.odo_anchor = odo          # start nebo skok (přesun, nahrání savu)
                elif odo - self.odo_anchor >= 0.05:
                    self.stats["km"] += odo - self.odo_anchor
                    self.odo_anchor = odo
                if self.fuel_anchor is None or fuel > self.fuel_anchor + 1:
                    self.fuel_anchor = fuel        # tankování
                elif self.fuel_anchor - fuel >= 0.05:
                    self.stats["fuel_l"] += self.fuel_anchor - fuel
                    self.fuel_anchor = fuel
                kmh = abs(d["speed"]) * 3.6
                if kmh > 1:
                    self.stats["drive_s"] += dt
                    self.stats["speed_int"] = self.stats.get("speed_int", 0.0) + kmh * dt
                if d["speedLimit"] > 0 and kmh > d["speedLimit"] * 3.6 + 5:
                    self.stats["speeding_s"] += dt
                self.stats["max_kmh"] = max(self.stats["max_kmh"], kmh)
            self.prev = d
            self.view = self._build(d)
            if now - self.last_save > 30 or self.pending:
                self.save(); self.last_save = now

    DAMAGE_PARTS = (("Motor", "wearEngine"), ("Převodovka", "wearTransmission"), ("Kabina", "wearCabin"),
                    ("Podvozek", "wearChassis"), ("Kola", "wearWheels"), ("Náklad", "cargoDamage"))
    TRAILER_PARTS = (("Návěs – podvozek", "trailerWearChassis"), ("Návěs – kola", "trailerWearWheels"),
                     ("Návěs – nástavba", "trailerWearBody"))

    def _check_damage(self, d, now):
        """Náraz = skokový nárůst poškození. Běžné opotřebení roste nepatrně, to ignorujeme."""
        p = self.prev
        parts = list(self.DAMAGE_PARTS)
        if d["trailerAttached"] and p.get("trailerAttached") and d["trailerName"] == p.get("trailerName"):
            parts += self.TRAILER_PARTS
        hit = False
        for name, k in parts:
            delta = d[k] - p.get(k, d[k])
            if 0 < delta < 0.3:          # >30 % naráz = spíš nahraný save než náraz
                if delta >= 0.0005:
                    hit = True
                self.dmg_acc[name] = self.dmg_acc.get(name, 0) + delta
        if hit:
            self.dmg_t = now
        elif self.dmg_acc and now - self.dmg_t > 1.0:
            big = {n: v for n, v in self.dmg_acc.items() if v >= 0.002}
            self.dmg_acc = {}
            if big and self.dmg_t:
                txt = ", ".join(f"{n} +{v * 100:.1f} %".replace(".", ",") for n, v in big.items())
                self._log("dmg", f"Poškození: {txt}")
                self.last_damage = now
            self.dmg_t = 0.0

    # ---------- view model pro frontend ----------
    def _stats_view(self, cur):
        s = self.stats
        fines = sum(f["amount"] for f in s["fines"])
        transport = sum(t["amount"] for t in s["transport"])
        income = sum(j["revenue"] for j in s["jobs"])
        return {
            "since": s["since"], "km": s["km"], "fuel_l": s["fuel_l"],
            "avg_l100": s["fuel_l"] / s["km"] * 100 if s["km"] > 1 else None,
            "drive_s": s["drive_s"], "avg_kmh": s.get("speed_int", 0) / s["drive_s"] if s["drive_s"] > 30 else None,
            "speeding_s": s["speeding_s"], "max_kmh": s["max_kmh"],
            "fines_n": len(s["fines"]), "fines_sum": fines,
            "tolls_n": s["tolls_n"], "tolls_sum": s["tolls_sum"],
            "transport_n": len(s["transport"]), "transport_sum": transport,
            "jobs_ok": sum(1 for j in s["jobs"] if j["ok"]), "income": income,
            "net": income - fines - s["tolls_sum"] - transport,
            "per_hour": (income - fines - s["tolls_sum"] - transport) / (s["drive_s"] / 3600)
            if s["drive_s"] > 600 else None,
            "jobs": s["jobs"][:6], "log": s["log"][:12], "rate": self.rate,
        }

    def _build(self, d):
        cur_scale = d["scale"] if d["scale"] > 0 else 19.0
        # Ve městech hra zpomaluje čas na 1:3. Pro přepočet dlouhých časů (ETA, termín, pauza)
        # proto bereme "silniční" měřítko: nejvyšší viděné v této herní relaci, dokud jsme
        # viděli jen město, výchozí hodnotu hry (ETS2 19, ATS 20).
        self.road_scale = max(getattr(self, "road_scale", 0), cur_scale)
        default = 20.0 if d["game"] == 2 else 19.0
        scale = self.road_scale if self.road_scale > 3 else default
        route_ok = d["routeDistance"] > 50
        real_eta = d["routeTime"] / scale if route_ok else None
        deadline = d["timeAbsDelivery"] - d["timeAbs"] if d["onJob"] and not d["specialJob"] else None
        g = d["gearDashboard"]
        gear = "N" if g == 0 else (f"R{-g}" if g < 0 else str(g))
        return {
            "connected": True, "paused": d["paused"],
            "game": {1: "ETS2", 2: "ATS"}.get(d["game"], "?"),
            "rate": self.usd if d["game"] == 2 else self.rate,
            "timeAbs": d["timeAbs"], "scale": scale, "curScale": cur_scale,
            "speed": abs(d["speed"]) * 3.6, "limit": d["speedLimit"] * 3.6,
            "cruise": d["cruiseControlSpeed"] * 3.6 if d["cruiseControl"] else None,
            "gear": gear, "shifter": d["shifterType"],
            "rpm": d["engineRpm"], "rpmMax": d["engineRpmMax"],
            "retarder": d["retarderBrake"], "retarderMax": d["retarderStepCount"],
            "fuel": d["fuel"], "fuelCap": d["fuelCapacity"], "fuelRange": d["fuelRange"],
            "fuelAvg": d["fuelAvgConsumption"] * 100, "adblue": d["adblue"], "adblueCap": d["adblueCapacity"],
            "air": d["airPressure"], "brakeTemp": d["brakeTemperature"], "oilTemp": d["oilTemperature"],
            "oilPress": d["oilPressure"], "waterTemp": d["waterTemperature"], "battery": d["batteryVoltage"],
            "warn": {k: d[k] for k in ("fuelWarning", "adblueWarning", "airPressureWarning",
                                       "oilPressureWarning", "waterTemperatureWarning", "batteryVoltageWarning")},
            "odo": d["truckOdometer"],
            "lights": {k: d[k] for k in ("parkBrake", "engineEnabled", "lightsBeamLow", "lightsBeamHigh",
                                         "lightsBeacon", "lightsHazard", "wipers", "blinkerLeftOn",
                                         "blinkerRightOn", "differentialLock", "liftAxle", "motorBrake")},
            "route": {"km": d["routeDistance"] / 1000, "gameMin": d["routeTime"] / 60,
                      "realS": real_eta, "arrival": time.time() + real_eta if real_eta else None}
            if route_ok else None,
            "rest": {"gameMin": d["restStop"], "realS": d["restStop"] * 60 / scale},
            "truck": {"name": f'{d["truckBrand"]} {d["truckName"]}'.strip(), "plate": d["truckLicensePlate"],
                      "wear": {"Motor": d["wearEngine"], "Převodovka": d["wearTransmission"],
                               "Kabina": d["wearCabin"], "Podvozek": d["wearChassis"], "Kola": d["wearWheels"]}},
            "trailer": {"name": f'{d["trailerBrand"]} {d["trailerName"]}'.strip(),
                        "wear": {"Podvozek": d["trailerWearChassis"], "Kola": d["trailerWearWheels"],
                                 "Nástavba": d["trailerWearBody"]}} if d["trailerAttached"] else None,
            "job": {"from": d["citySrc"], "to": d["cityDst"], "compFrom": d["compSrc"], "compTo": d["compDst"],
                    "cargo": d["cargo"], "mass": d["cargoMass"], "income": d["jobIncome"],
                    "damage": d["cargoDamage"], "plannedKm": d["plannedDistanceKm"],
                    "deadlineMin": deadline, "special": d["specialJob"], "market": d["jobMarket"]}
            if d["onJob"] else None,
            "stats": self._stats_view(d),
            "plan": self._plan(d, route_ok, deadline),
            "damageFlash": time.time() - self.last_damage < 4,
            "delivery": self.delivery if self.delivery and time.time() - self.delivery["t"] < 25 else None,
        }

    def _plan(self, d, route_ok, deadline):
        if not route_ok:
            return None
        route_min = d["routeTime"] / 60
        rest = d["restStop"]
        sleeps = 0 if route_min <= rest else math.ceil((route_min - max(rest, 0)) / DRIVE_AFTER_SLEEP_MIN)
        route_km = d["routeDistance"] / 1000
        return {
            "sleeps": sleeps,
            "shortMin": route_min - max(rest, 0),   # kolik herního času chybí k dojetí bez spánku
            "fuelOk": d["fuelRange"] >= route_km * 1.05,
            "fuelRange": d["fuelRange"],
            "bufferMin": deadline - route_min if deadline is not None else None,
        }

    def snapshot(self):
        with self.lock:
            return json.dumps(self.view, ensure_ascii=False)


# --------------------------------------------------------------------------
#  HTTP server (SSE stream, statické soubory)
# --------------------------------------------------------------------------
def make_handler(proc, allow_lan):
    page = os.path.join(HERE, "dashboard.html")

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _host_ok(self):
            if allow_lan:
                return True
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
            return host in ("127.0.0.1", "localhost", "[::1]")  # ochrana proti DNS rebindingu

        def do_GET(self):
            if not self._host_ok():
                return self.send_error(403)
            if self.path in ("/", "/index.html"):
                with open(page, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/history":
                body = proc.history().encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/events":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                try:
                    while True:
                        self.wfile.write(f"data: {proc.snapshot()}\n\n".encode())
                        self.wfile.flush()
                        time.sleep(0.25)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    return
            else:
                self.send_error(404)

        def do_POST(self):
            # vlastní hlavička => cizí web ji přes CORS nepošle (bez preflightu neprojde)
            if not self._host_ok() or self.headers.get("X-Dash") != "1":
                return self.send_error(403)
            if self.path == "/api/reset":
                proc.reset()
                self.send_response(204)
                self.end_headers()
            else:
                self.send_error(404)

    return H


def main():
    if sys.stdout is None:
        # spuštěno přes pythonw (bez konzole) -> výpisy a chyby jdou do dash.log
        log = open(os.path.join(HERE, "dash.log"), "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stderr = log
        print(f"--- start {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    ap = argparse.ArgumentParser(description="Lokální ETS2/ATS dashboard")
    ap.add_argument("--port", type=int, default=8088)
    ap.add_argument("--lan", action="store_true", help="naslouchat na všech rozhraních (jinak jen 127.0.0.1)")
    ap.add_argument("--demo", action="store_true", help="simulovaná data bez hry")
    ap.add_argument("--rate", type=float, default=24.4945, help="kurz EUR→CZK (výchozí = kurz, který používá ETS2)")
    ap.add_argument("--usd", type=float, default=21.0, help="kurz USD→CZK (ATS)")
    ap.add_argument("--exit-with-game", action="store_true", help="ukončit dashboard po zavření hry")
    ap.add_argument("--keep", action="store_true", help="nenulovat statistiky při novém spuštění hry")
    a = ap.parse_args()

    src = DemoSource() if a.demo else SharedMemorySource()
    proc = Processor(src, a.rate, a.usd, auto_reset=not a.keep)

    def loop():
        while True:
            try:
                proc.tick()
            except Exception as e:  # noqa: BLE001 - dashboard nesmí spadnout kvůli jednomu špatnému čtení
                print("Chyba čtení telemetrie:", e)
            time.sleep(0.1)

    threading.Thread(target=loop, daemon=True).start()
    bind = "0.0.0.0" if a.lan else "127.0.0.1"
    srv = ThreadingHTTPServer((bind, a.port), make_handler(proc, a.lan))
    srv.daemon_threads = True
    if a.exit_with_game:
        def watch():
            proc.game_exited.wait()
            print("Hra ukončena, vypínám dashboard.")
            srv.shutdown()
        threading.Thread(target=watch, daemon=True).start()
    print(f"Dashboard běží na http://127.0.0.1:{a.port}  ({'LAN' if a.lan else 'jen localhost'}"
          f"{', DEMO' if a.demo else ''})  – Ctrl+C ukončí")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        with proc.lock:
            proc.save()
        srv.server_close()


if __name__ == "__main__":
    main()
