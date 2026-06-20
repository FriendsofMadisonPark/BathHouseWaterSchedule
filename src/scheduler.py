from __future__ import annotations

from calendar import monthrange
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

WEEKDAY_NAMES = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}

DAY_LOOKUP = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


@dataclass(frozen=True)
class Zone:
    name: str
    days: tuple[int, ...]
    minutes: int


DEFAULT_ZONES: tuple[Zone, ...] = (
    Zone(name="North Lawn", days=(0, 3), minutes=35),
    Zone(name="Playground Beds", days=(1, 4), minutes=25),
    Zone(name="South Garden", days=(2, 5), minutes=30),
    Zone(name="Perimeter Trees", days=(6,), minutes=45),
)


def _parse_iso_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("start_date must be in YYYY-MM-DD format") from exc


def month_plan_range(start_date: str) -> tuple[str, int]:
    start = _parse_iso_date(start_date)
    first_day = start.replace(day=1)
    return first_day.strftime("%Y-%m-%d"), monthrange(start.year, start.month)[1]


def parse_days(day_values: Iterable[str]) -> tuple[int, ...]:
    parsed: list[int] = []
    for day in day_values:
        key = day.strip().lower()
        if key not in DAY_LOOKUP:
            raise ValueError(f"Unknown day value: {day}")
        parsed.append(DAY_LOOKUP[key])
    return tuple(sorted(set(parsed)))


def load_zones_from_json(config_path: str) -> tuple[Zone, ...]:
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    if not isinstance(raw, dict) or "zones" not in raw:
        raise ValueError("Zone config must be an object with a 'zones' key")

    zone_items = raw["zones"]
    if not isinstance(zone_items, list):
        raise ValueError("'zones' must be a list")

    zones: list[Zone] = []
    for item in zone_items:
        if not isinstance(item, dict):
            raise ValueError("Each zone entry must be an object")

        name = item.get("name")
        days = item.get("days")
        minutes = item.get("minutes")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Each zone must include a non-empty 'name'")
        if not isinstance(days, list) or not all(isinstance(day, str) for day in days):
            raise ValueError("Each zone must include a string list for 'days'")
        if not isinstance(minutes, int) or minutes <= 0:
            raise ValueError("Each zone must include a positive integer 'minutes'")

        zones.append(Zone(name=name.strip(), days=parse_days(days), minutes=minutes))

    return tuple(zones)


def load_date_overrides_from_json(config_path: str) -> dict[str, str]:
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    override_items = raw.get("date_overrides", {})
    if not isinstance(override_items, dict):
        raise ValueError("'date_overrides' must be an object when provided")

    overrides: dict[str, str] = {}
    for key, value in override_items.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("'date_overrides' keys and values must be strings")
        _parse_iso_date(key)
        if not value.strip():
            raise ValueError("Override values must be non-empty strings")
        overrides[key] = value.strip()

    return overrides


def generate_schedule(
    zones: Iterable[Zone],
    start_date: str,
    days: int,
    max_daily_minutes: int,
    date_overrides: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    if days <= 0:
        raise ValueError("days must be greater than 0")
    if max_daily_minutes <= 0:
        raise ValueError("max_daily_minutes must be greater than 0")

    start = _parse_iso_date(start_date)
    zone_list = list(zones)
    output: list[dict[str, object]] = []

    for offset in range(days):
        current = start + timedelta(days=offset)
        current_date = current.strftime("%Y-%m-%d")
        if date_overrides and current_date in date_overrides:
            output.append(
                {
                    "date": current_date,
                    "weekday": WEEKDAY_NAMES[current.weekday()],
                    "total_minutes": 0,
                    "zones": [date_overrides[current_date]],
                }
            )
            continue

        weekday = current.weekday()
        active: list[Zone] = [z for z in zone_list if weekday in z.days]

        total = 0
        selected: list[Zone] = []
        for zone in active:
            if total + zone.minutes <= max_daily_minutes:
                selected.append(zone)
                total += zone.minutes

        output.append(
            {
                "date": current_date,
                "weekday": WEEKDAY_NAMES[weekday],
                "total_minutes": total,
                "zones": [z.name for z in selected],
            }
        )

    return output


def format_schedule(schedule: Iterable[dict[str, object]]) -> str:
    lines = ["Madison Park Watering Schedule", "=" * 31]
    for row in schedule:
        zones = row["zones"]
        zone_text = ", ".join(zones) if zones else "No watering"
        lines.append(
            f"{row['date']} ({row['weekday']}): {zone_text} [{row['total_minutes']} min]"
        )
    return "\n".join(lines)
