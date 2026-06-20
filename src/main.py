from __future__ import annotations

import argparse
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path

try:
    from src.calendar_view import render_calendar_html, render_range_html, render_week_html
    from src.scheduler import (
        format_schedule,
        generate_schedule,
        load_date_overrides_from_json,
        load_zones_from_json,
    )
except ModuleNotFoundError:
    from calendar_view import render_calendar_html, render_range_html, render_week_html
    from scheduler import (
        format_schedule,
        generate_schedule,
        load_date_overrides_from_json,
        load_zones_from_json,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a watering schedule for Madison Park zones."
    )
    parser.add_argument(
        "--start-date",
        default=date.today().isoformat(),
        help="Schedule start date in YYYY-MM-DD format (default: today).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to plan (default: 30).",
    )
    parser.add_argument(
        "--max-minutes",
        type=int,
        default=120,
        help="Daily watering cap in minutes (default: 120).",
    )
    parser.add_argument(
        "--zones-file",
        default="config/zones.json",
        help="Path to JSON file containing zone definitions (default: config/zones.json).",
    )
    parser.add_argument(
        "--html-output",
        default="",
        help="Write a visual HTML calendar to this file path instead of only printing text.",
    )
    parser.add_argument(
        "--view",
        choices=["month", "week", "range"],
        default="month",
        help="Visual calendar type for HTML output: month, week, or range (default: month).",
    )
    parser.add_argument(
        "--week-start-sunday",
        action="store_true",
        help="For week view, shift start date back to the previous Sunday.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    zones = load_zones_from_json(args.zones_file)
    date_overrides = load_date_overrides_from_json(args.zones_file)
    start_date = args.start_date
    days = args.days

    if args.view == "week":
        week_start = date.fromisoformat(args.start_date)
        if args.week_start_sunday:
            # Convert weekday to distance from Sunday.
            shift = (week_start.weekday() + 1) % 7
            week_start = week_start - timedelta(days=shift)
        start_date = week_start.isoformat()
        days = 7
    elif args.view == "range":
        range_start = date.fromisoformat(args.start_date)
        if args.week_start_sunday:
            shift = (range_start.weekday() + 1) % 7
            range_start = range_start - timedelta(days=shift)
        start_date = range_start.isoformat()
        days = args.days
    elif args.html_output:
        start = date.fromisoformat(args.start_date)
        start_date = start.replace(day=1).isoformat()
        days = monthrange(start.year, start.month)[1]

    schedule = generate_schedule(
        zones=zones,
        start_date=start_date,
        days=days,
        max_daily_minutes=args.max_minutes,
        date_overrides=date_overrides,
    )
    print(format_schedule(schedule))
    if args.html_output:
        html_path = Path(args.html_output)
        if args.view == "week":
            html_content = render_week_html(schedule, start_date)
        elif args.view == "range":
            html_content = render_range_html(schedule, start_date)
        else:
            html_content = render_calendar_html(schedule, start_date)
        html_path.write_text(html_content, encoding="utf-8")
        print(f"Visual calendar written to {html_path}")


if __name__ == "__main__":
    main()
