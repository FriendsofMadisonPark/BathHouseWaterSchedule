from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from calendar_view import render_range_html
from scheduler import (
    generate_schedule,
    load_date_overrides_from_json,
    load_zones_from_json,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "zones.json"
SHARED_EDITS_PATH = Path(os.environ.get("BATHHOUSE_SHARED_EDITS_PATH", str(ROOT_DIR / "config" / "shared_edits.json")))
CALENDAR_PATH = ROOT_DIR / "calendar.html"


class CalendarSettings:
    def __init__(self, start_date: str, days: int, max_minutes: int) -> None:
        self.start_date = start_date
        self.days = days
        self.max_minutes = max_minutes


SETTINGS = CalendarSettings(start_date="2026-06-19", days=140, max_minutes=120)


def align_to_sunday(start_date: str) -> str:
    current = date.fromisoformat(start_date)
    shift = (current.weekday() + 1) % 7
    return (current - timedelta(days=shift)).isoformat()


def load_shared_edits() -> dict[str, str]:
    if not SHARED_EDITS_PATH.exists():
        return {}
    with SHARED_EDITS_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    edits = data.get("edits", {})
    if not isinstance(edits, dict):
        return {}
    return {str(key): str(value) for key, value in edits.items()}


def save_shared_edits(edits: dict[str, str]) -> None:
    SHARED_EDITS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SHARED_EDITS_PATH.open("w", encoding="utf-8") as file:
        json.dump({"edits": edits}, file, indent=2)


def generate_calendar_file() -> None:
    zones = load_zones_from_json(str(CONFIG_PATH))
    base_overrides = load_date_overrides_from_json(str(CONFIG_PATH))
    shared_edits = load_shared_edits()
    merged_overrides = {**base_overrides, **shared_edits}

    start_date = align_to_sunday(SETTINGS.start_date)
    schedule = generate_schedule(
        zones=zones,
        start_date=start_date,
        days=SETTINGS.days,
        max_daily_minutes=SETTINGS.max_minutes,
        date_overrides=merged_overrides,
    )
    html = render_range_html(schedule, start_date)
    CALENDAR_PATH.write_text(html, encoding="utf-8")


class SharedCalendarHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, html: str) -> None:
        raw = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path in ("/", "/calendar.html"):
            generate_calendar_file()
            self._send_html(CALENDAR_PATH.read_text(encoding="utf-8"))
            return

        if self.path == "/api/edits":
            self._send_json({"edits": load_shared_edits()})
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:
        if self.path != "/api/edits":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            self.send_error(HTTPStatus.BAD_REQUEST, "Request body required")
            return

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
            return

        day = payload.get("date")
        value = payload.get("value")
        if not isinstance(day, str) or not isinstance(value, str):
            self.send_error(HTTPStatus.BAD_REQUEST, "date and value must be strings")
            return

        try:
            datetime.strptime(day, "%Y-%m-%d")
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST, "date must be YYYY-MM-DD")
            return

        edits = load_shared_edits()
        edits[day] = value.strip() or "Coverage Needed"
        save_shared_edits(edits)
        self._send_json({"ok": True, "edits": edits})

    def log_message(self, format: str, *args) -> None:
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run shared editable calendar server.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000).")
    parser.add_argument(
        "--start-date",
        default=SETTINGS.start_date,
        help="Schedule start date in YYYY-MM-DD (default: 2026-06-19).",
    )
    parser.add_argument("--days", type=int, default=SETTINGS.days, help="Number of days to plan (default: 140).")
    parser.add_argument(
        "--max-minutes",
        type=int,
        default=SETTINGS.max_minutes,
        help="Daily minutes cap for scheduler (default: 120).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    SETTINGS.start_date = args.start_date
    SETTINGS.days = args.days
    SETTINGS.max_minutes = args.max_minutes

    SHARED_EDITS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SHARED_EDITS_PATH.exists():
        save_shared_edits({})

    generate_calendar_file()
    server = ThreadingHTTPServer((args.host, args.port), SharedCalendarHandler)
    print(f"Using shared edits file: {SHARED_EDITS_PATH}")
    print(f"Shared calendar server running at http://{args.host}:{args.port}")
    print("Open / on any device on the same network to view and edit.")
    server.serve_forever()


if __name__ == "__main__":
    main()
