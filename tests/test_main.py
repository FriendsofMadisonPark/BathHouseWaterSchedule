import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.calendar_view import render_calendar_html
from src.scheduler import Zone, generate_schedule, load_zones_from_json, month_plan_range


class SchedulerTests(unittest.TestCase):
    def test_generate_schedule_includes_matching_zones(self):
        zones = (
            Zone(name="A", days=(0,), minutes=30),
            Zone(name="B", days=(0,), minutes=40),
            Zone(name="C", days=(1,), minutes=20),
        )
        schedule = generate_schedule(
            zones=zones,
            start_date="2026-06-22",
            days=2,
            max_daily_minutes=60,
        )

        self.assertEqual(schedule[0]["zones"], ["A"])
        self.assertEqual(schedule[0]["total_minutes"], 30)
        self.assertEqual(schedule[1]["zones"], ["C"])

    def test_generate_schedule_rejects_invalid_days(self):
        with self.assertRaises(ValueError):
            generate_schedule(
                zones=(),
                start_date="2026-06-22",
                days=0,
                max_daily_minutes=60,
            )

    def test_generate_schedule_applies_date_override(self):
        zones = (
            Zone(name="Kevin", days=(2,), minutes=45),
        )
        schedule = generate_schedule(
            zones=zones,
            start_date="2026-07-01",
            days=1,
            max_daily_minutes=60,
            date_overrides={"2026-07-01": "Coverage Needed"},
        )

        self.assertEqual(schedule[0]["zones"], ["Coverage Needed"])

    def test_load_zones_from_json(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "zones.json"
            config_path.write_text(
                """
{
    "zones": [
        {"name": "Demo Zone", "days": ["Mon", "Thu"], "minutes": 20}
    ]
}
""".strip(),
                encoding="utf-8",
            )

            zones = load_zones_from_json(str(config_path))

        self.assertEqual(len(zones), 1)
        self.assertEqual(zones[0].name, "Demo Zone")
        self.assertEqual(zones[0].days, (0, 3))
        self.assertEqual(zones[0].minutes, 20)

    def test_load_zones_from_json_rejects_unknown_day(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "zones.json"
            config_path.write_text(
                """
{
    "zones": [
        {"name": "Bad Zone", "days": ["Funday"], "minutes": 20}
    ]
}
""".strip(),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_zones_from_json(str(config_path))

    def test_render_calendar_html_contains_month_and_zone(self):
        schedule = generate_schedule(
            zones=(Zone(name="Demo", days=(4,), minutes=25),),
            start_date="2026-06-19",
            days=30,
            max_daily_minutes=60,
        )

        html = render_calendar_html(schedule, "2026-06-19")

        self.assertIn("Madison Park Watering Calendar", html)
        self.assertIn("Demo", html)
        self.assertIn("June 2026", html)

    def test_month_plan_range_uses_first_day_and_month_length(self):
        start_date, days = month_plan_range("2026-06-19")

        self.assertEqual(start_date, "2026-06-01")
        self.assertEqual(days, 30)


if __name__ == "__main__":
    unittest.main()
