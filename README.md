# Madison Park Watering Schedule

A Python CLI that generates a day-by-day watering plan for Madison Park zones.
Zone definitions are loaded from a JSON config file so you can update schedules without editing code.
You can also generate a visual HTML calendar view.

## Run

```bash
python src/main.py
```

## Options

```bash
python src/main.py --start-date 2026-06-19 --days 10 --max-minutes 90
```

- `--start-date`: start date in `YYYY-MM-DD`.
- `--days`: number of calendar days to plan, defaulting to 30.
- `--max-minutes`: daily watering cap; zones beyond the cap are skipped.
- `--zones-file`: path to zone config JSON (default: `config/zones.json`).
- `--html-output`: write a visual calendar to an HTML file.
- `--view`: `month`, `week`, or `range` visual output mode.
- `--week-start-sunday`: in week mode, aligns the 7-day view to Sunday.

## Zone Config

Edit `config/zones.json` to manage watering zones.

Example entry:

```json
{
	"name": "North Lawn",
	"days": ["Mon", "Thu"],
	"minutes": 35
}
```

## Visual Calendar

Generate a browser-ready calendar:

```bash
python src/main.py --start-date 2026-06-19 --days 14 --html-output calendar.html
```

When `--html-output` is used, the app renders the full month containing `--start-date`.
Then open `calendar.html` in your browser.

## Shared Multi-User Editing

Run the shared server so multiple people can edit individual cells and see the same updates:

```bash
python src/shared_server.py --host 0.0.0.0 --port 8000 --start-date 2026-06-19 --days 140
```

Then open:

- On your computer: `http://localhost:8000`
- On phones on the same Wi-Fi: `http://<your-computer-ip>:8000`

Notes:

- Cell edits are shared through `config/shared_edits.json`.
- `Coverage Needed` values are shown in red.

Generate a 7-day calendar starting on Sunday:

```bash
python src/main.py --start-date 2026-06-19 --view week --week-start-sunday --html-output calendar.html
```

Generate a rolling 30-day calendar in a 4-5 week layout:

```bash
python src/main.py --start-date 2026-06-19 --days 30 --view range --week-start-sunday --html-output calendar.html
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

