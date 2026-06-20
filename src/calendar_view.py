from __future__ import annotations

from calendar import Calendar, monthcalendar, month_name
from datetime import date, datetime, timedelta
from html import escape


def render_calendar_html(schedule: list[dict[str, object]], start_date: str) -> str:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    month_grid = monthcalendar(start.year, start.month)
    schedule_by_date = {row["date"]: row for row in schedule}

    day_headers = "".join(f"<th>{escape(day)}</th>" for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    weeks_html: list[str] = []

    for week in month_grid:
        cells: list[str] = []
        for day in week:
            if day == 0:
                cells.append('<td class="empty"></td>')
                continue

            date_text = f"{start.year}-{start.month:02d}-{day:02d}"
            row = schedule_by_date.get(date_text)
            if row is None:
                cells.append(
                    f'<td><div class="day-num">{day}</div><div class="event none">No watering</div></td>'
                )
                continue

            zones = row["zones"]
            zone_html = "<br>".join(escape(zone) for zone in zones) if zones else "No watering"
            minutes = row["total_minutes"]
            cells.append(
                f'<td><div class="day-num">{day}</div><div class="event"><strong>{zone_html}</strong><span>{minutes} min</span></div></td>'
            )

        weeks_html.append(f"<tr>{''.join(cells)}</tr>")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Madison Park Watering Calendar</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f3f1e7;
      --panel: #fffdf7;
      --ink: #1f2933;
      --muted: #667085;
      --line: #d9d4c4;
      --accent: #2f6f4f;
      --accent-soft: #dbe9df;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: linear-gradient(180deg, #f8f6ef 0%, #ebe5d6 100%);
      color: var(--ink);
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 48px; }}
    .hero {{
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 24px;
      margin-bottom: 20px;
    }}
    h1 {{ margin: 0; font-size: clamp(2rem, 4vw, 3.4rem); line-height: 1; }}
    .subtitle {{ margin: 8px 0 0; color: var(--muted); }}
    .badge {{
      padding: 10px 14px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 700;
      white-space: nowrap;
    }}
    .calendar {{ width: 100%; border-collapse: separate; border-spacing: 10px; table-layout: fixed; }}
    .calendar th {{ color: var(--muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.12em; }}
    .calendar td {{ vertical-align: top; min-height: 138px; background: var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 12px; box-shadow: 0 8px 24px rgba(24, 30, 20, 0.05); }}
    .empty {{ background: transparent; border: none; box-shadow: none; }}
    .day-num {{ font-size: 1.15rem; font-weight: 700; margin-bottom: 10px; }}
    .event {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding: 10px;
      border-radius: 14px;
      background: linear-gradient(180deg, #edf5ef 0%, #dce9df 100%);
      border-left: 5px solid var(--accent);
      min-height: 74px;
    }}
    .event.none {{ background: #f5f3ee; border-left-color: #c1b8a0; color: var(--muted); }}
    .event strong {{ font-size: 0.98rem; line-height: 1.2; }}
    .event span {{ font-size: 0.85rem; color: var(--muted); }}
    .legend {{ margin-top: 18px; color: var(--muted); font-size: 0.95rem; }}
    @media (max-width: 900px) {{
      .hero {{ flex-direction: column; align-items: start; }}
      .calendar, .calendar tbody, .calendar tr, .calendar td {{ display: block; width: 100%; }}
      .calendar thead {{ display: none; }}
      .calendar tr {{ margin-bottom: 12px; }}
      .calendar td {{ min-height: auto; margin-bottom: 10px; }}
      .empty {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div>
        <h1>Madison Park Watering Calendar</h1>
        <p class="subtitle">{escape(month_name[start.month])} {start.year} visual schedule</p>
      </div>
      <div class="badge">Watering plan</div>
    </div>
    <table class="calendar" aria-label="Watering calendar">
      <thead><tr>{day_headers}</tr></thead>
      <tbody>
        {''.join(weeks_html)}
      </tbody>
    </table>
    <div class="legend">Each day shows scheduled zones and total watering minutes. Days outside the configured window are shown as no watering.</div>
  </div>
</body>
</html>"""


def render_week_html(schedule: list[dict[str, object]], start_date: str) -> str:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    schedule_by_date = {row["date"]: row for row in schedule}
    days_html: list[str] = []

    for offset in range(7):
        current = start + timedelta(days=offset)
        date_text = current.strftime("%Y-%m-%d")
        weekday = current.strftime("%A")
        row = schedule_by_date.get(date_text)
        zones = row["zones"] if row else []
        minutes = row["total_minutes"] if row else 0
        zone_html = "<br>".join(escape(zone) for zone in zones) if zones else "No watering"

        days_html.append(
            f"""
            <article class=\"day-card\">
              <h2>{escape(weekday)}</h2>
              <p class=\"date\">{date_text}</p>
              <div class=\"event\"><strong>{zone_html}</strong><span>{minutes} min</span></div>
            </article>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Madison Park 7-Day Watering Calendar</title>
  <style>
    :root {{
      --bg: #f3f1e7;
      --panel: #fffdf7;
      --ink: #1f2933;
      --muted: #667085;
      --line: #d9d4c4;
      --accent: #2f6f4f;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: linear-gradient(180deg, #f8f6ef 0%, #ebe5d6 100%);
      color: var(--ink);
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 28px 18px 36px; }}
    h1 {{ margin: 0 0 10px; font-size: clamp(1.8rem, 3.5vw, 3rem); }}
    .sub {{ margin: 0 0 20px; color: var(--muted); }}
    .week-wrap {{ overflow-x: auto; padding-bottom: 8px; }}
    .week {{
      display: grid;
      grid-template-columns: repeat(7, minmax(145px, 1fr));
      gap: 12px;
      min-width: 1080px;
    }}
    .day-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 12px;
      box-shadow: 0 8px 24px rgba(24, 30, 20, 0.05);
      min-height: 150px;
    }}
    .day-card h2 {{ margin: 0; font-size: 1.1rem; }}
    .date {{ margin: 4px 0 10px; color: var(--muted); font-size: 0.9rem; }}
    .event {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      background: linear-gradient(180deg, #edf5ef 0%, #dce9df 100%);
      border-left: 5px solid var(--accent);
      border-radius: 12px;
      padding: 10px;
      min-height: 72px;
    }}
    .event strong {{ font-size: 0.95rem; }}
    .event span {{ color: var(--muted); font-size: 0.86rem; }}
    @media (max-width: 1100px) {{
      .wrap {{ padding: 20px 12px 28px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Madison Park 7-Day Watering Calendar</h1>
    <p class="sub">Sunday-start weekly view</p>
    <div class="week-wrap">
      <section class="week">
        {''.join(days_html)}
      </section>
    </div>
  </div>
</body>
</html>"""


def render_range_html(schedule: list[dict[str, object]], start_date: str) -> str:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    today = date.today()
    schedule_by_date = {row["date"]: row for row in schedule}
    days = len(schedule)
    start_month = start.month
    end = start + timedelta(days=max(days - 1, 0))
    day_headers = "".join(
        f"<th>{escape(day)}</th>" for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    )
    cal = Calendar(firstweekday=6)

    month_keys: list[tuple[int, int]] = []
    cursor = date(start.year, start.month, 1)
    end_month = date(end.year, end.month, 1)
    while cursor <= end_month:
        month_keys.append((cursor.year, cursor.month))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)

    month_sections: list[str] = []
    for year, month in month_keys:
        rows_html: list[str] = []
        for week in cal.monthdatescalendar(year, month):
            cells: list[str] = []
            all_outside_plan = True
            for current_day in week:
                if current_day.month != month:
                    cells.append('<td class="empty"></td>')
                    continue

                date_text = current_day.isoformat()
                is_past = current_day < today
                past_class = " past" if is_past else ""
                row = schedule_by_date.get(date_text)
                if row is None:
                    cells.append(
                        f'<td class="empty{past_class}"><div class="day-num">{current_day.day}</div><div class="event none"><strong>Outside Plan</strong></div></td>'
                    )
                    continue

                all_outside_plan = False
                zones = row["zones"] if row else []
                zone_html = escape(zones[0]) if zones else "Coverage Needed"
                event_class = "event july editable" if month != start_month else "event editable"
                if zone_html.lower() == "coverage needed":
                    event_class = f"{event_class} coverage"
                cells.append(
                  f'<td class="editable-cell{past_class}" data-date="{date_text}" data-editable="true"><div class="day-num">{current_day.day}</div><div class="{event_class}" data-date="{date_text}" data-editable="true"><strong>{zone_html}</strong></div></td>'
                )

            if not all_outside_plan:
                rows_html.append(f"<tr>{''.join(cells)}</tr>")

        month_sections.append(
            f"""
            <section class=\"month-block\">
              <h2>{escape(month_name[month])} {year}</h2>
              <div class=\"calendar-wrap\">
                <table class=\"calendar\" aria-label=\"{escape(month_name[month])} {year} watering calendar\">
                  <thead><tr>{day_headers}</tr></thead>
                  <tbody>{''.join(rows_html)}</tbody>
                </table>
              </div>
            </section>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Madison Park 30-Day Calendar</title>
  <style>
    :root {{
      color-scheme: light;
      --panel: #fffdf7;
      --ink: #1f2933;
      --muted: #667085;
      --line: #d9d4c4;
      --accent: #2f6f4f;
      --accent-soft: #dbe9df;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: linear-gradient(180deg, #f8f6ef 0%, #ebe5d6 100%);
      color: var(--ink);
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 28px 18px 36px; }}
    .hero {{ display: flex; justify-content: space-between; align-items: end; gap: 20px; margin-bottom: 20px; }}
    h1 {{ margin: 0; font-size: clamp(2rem, 4vw, 3.2rem); }}
    .sub {{ margin: 8px 0 0; color: var(--muted); }}
    .badge {{ padding: 10px 14px; border-radius: 999px; background: var(--accent-soft); color: var(--accent); font-weight: 700; }}
    .month-block {{ margin-top: 20px; }}
    .month-block h2 {{ margin: 0 0 10px; font-size: 1.45rem; }}
    .calendar-wrap {{ overflow-x: auto; padding-bottom: 8px; }}
    .calendar {{ width: 100%; min-width: 1080px; border-collapse: separate; border-spacing: 10px; table-layout: fixed; }}
    .calendar th {{ color: var(--muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.12em; }}
    .calendar td {{ vertical-align: middle; background: var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 12px; box-shadow: 0 8px 24px rgba(24, 30, 20, 0.05); min-height: 110px; }}
    .calendar td.editable-cell {{ cursor: pointer; }}
    .calendar td.empty {{ background: transparent; border: none; box-shadow: none; }}
    .day-num {{ font-size: 0.9rem; color: var(--muted); font-weight: 700; margin-bottom: 8px; }}
    .event {{ display: flex; align-items: center; justify-content: center; text-align: center; border-left: 5px solid var(--accent); border-radius: 12px; padding: 14px 10px; background: linear-gradient(180deg, #edf5ef 0%, #dce9df 100%); min-height: 80px; }}
    .event.july {{ background: linear-gradient(180deg, #d8ebde 0%, #bddfca 100%); border-left-color: #236243; }}
    .event.coverage {{ background: linear-gradient(180deg, #fbe5e6 0%, #f3c3c6 100%); border-left-color: #b4232f; }}
    .event.editable {{ cursor: pointer; }}
    .event strong {{ font-size: 1.05rem; letter-spacing: 0.02em; }}
    .event.none {{ background: #f5f3ee; border-left-color: #c1b8a0; }}
    .calendar td.past .day-num,
    .calendar td.past .event strong {{ color: #999999; }}
    @media (max-width: 900px) {{
      .hero {{ flex-direction: column; align-items: start; }}
      .wrap {{ padding: 20px 12px 28px; }}
      .calendar-wrap {{ overflow-x: hidden; padding-bottom: 0; }}
      .calendar {{ min-width: 0; border-spacing: 4px; }}
      .calendar th {{ font-size: 0.58rem; letter-spacing: 0.04em; }}
      .calendar td {{ padding: 4px; border-radius: 10px; min-height: 64px; }}
      .day-num {{ font-size: 0.62rem; margin-bottom: 4px; }}
      .event {{ min-height: 44px; padding: 6px 4px; border-left-width: 3px; border-radius: 8px; }}
      .event strong {{ font-size: 0.56rem; line-height: 1.05; word-break: break-word; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div>
        <h1>Madison Park 30-Day Calendar</h1>
        <p class="sub">{start.strftime('%B %Y')}</p>
        <p class="sub">{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}</p>
      </div>
      <div class="badge">Rolling plan</div>
    </div>
    {''.join(month_sections)}
  </div>
  <script>
    (() => {{
      const key = "mpws-cell-edits-v1";
      const parseLocalEdits = () => {{
        try {{
          return JSON.parse(localStorage.getItem(key) || "{{}}");
        }} catch (_err) {{
          return {{}};
        }}
      }};

      const saveLocalEdits = (edits) => {{
        localStorage.setItem(key, JSON.stringify(edits));
      }};

      const canUseSharedApi = window.location.protocol.startsWith("http");

      const fetchSharedEdits = async () => {{
        if (!canUseSharedApi) return null;
        try {{
          const res = await fetch("/api/edits", {{ cache: "no-store" }});
          if (!res.ok) return null;
          const payload = await res.json();
          return payload && typeof payload.edits === "object" ? payload.edits : null;
        }} catch (_err) {{
          return null;
        }}
      }};

      const saveSharedEdit = async (date, value) => {{
        if (!canUseSharedApi) return false;
        try {{
          const res = await fetch("/api/edits", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ date, value }}),
          }});
          return res.ok;
        }} catch (_err) {{
          return false;
        }}
      }};

      const setLabel = (cellEl, label) => {{
        const eventEl = cellEl.querySelector('.event[data-date][data-editable="true"]');
        if (!eventEl) return;
        const strong = eventEl.querySelector("strong");
        if (!strong) return;
        strong.textContent = label;
        if (label.trim().toLowerCase() === "coverage needed") {{
          eventEl.classList.add("coverage");
        }} else {{
          eventEl.classList.remove("coverage");
        }}
      }};

      const localEdits = parseLocalEdits();
      let sharedEdits = null;
      const editable = document.querySelectorAll('td[data-date][data-editable="true"]');
      const byDate = {{}};
      editable.forEach((cellEl) => {{
        const date = cellEl.getAttribute("data-date");
        if (!date) return;
        byDate[date] = cellEl;
      }});

      const applyEdits = (edits) => {{
        if (!edits || typeof edits !== "object") return;
        Object.entries(edits).forEach(([date, label]) => {{
          const cellEl = byDate[date];
          if (!cellEl || typeof label !== "string") return;
          setLabel(cellEl, label);
        }});
      }};

      applyEdits(localEdits);

      fetchSharedEdits().then((edits) => {{
        if (!edits) return;
        sharedEdits = edits;
        applyEdits(sharedEdits);
      }});

      editable.forEach((cellEl) => {{
        const date = cellEl.getAttribute("data-date");
        if (!date) return;

        cellEl.addEventListener("click", async () => {{
          const current = cellEl.querySelector("strong")?.textContent?.trim() || "";
          const next = window.prompt(`Edit assignee for ${{date}}`, current);
          if (next === null) return;
          const value = next.trim() || "Coverage Needed";

          localEdits[date] = value;
          saveLocalEdits(localEdits);
          setLabel(cellEl, value);

          const sharedSaved = await saveSharedEdit(date, value);
          if (sharedSaved && sharedEdits) {{
            sharedEdits[date] = value;
          }}
        }});
      }});
    }})();
  </script>
</body>
</html>"""