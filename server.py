import json
import re
from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("london-grapple")

MATS = {
    "1": {
        "name": "Mat 1 (HQ)",
        "url": "https://app.gymdesk.com/widgets/schedule/render/gym/D8eb1?visible_schedule=6X8d8&program=all&default_schedule=6X8d8",
    },
    "2": {
        "name": "Mat 2",
        "url": "https://app.gymdesk.com/widgets/schedule/render/gym/D8eb1?visible_schedule=D8pqo&program=all&default_schedule=D8pqo",
    },
}


def _parse_schedule(html: str, mat_key: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    events = soup.select(".schedule-event")
    results = []
    for ev in events:
        title_el = ev.select_one("h3")
        title = title_el.get_text(strip=True) if title_el else ""

        datetime_el = ev.select_one(".date-time")
        datetime_text = datetime_el.get_text(" ", strip=True) if datetime_el else ""

        # Parse "Monday, March 16 · 6:45am - 7:45am"
        day_name = ""
        date_str = ""
        time_range = ""
        if datetime_text:
            # Split on the dot/middot separator
            parts = re.split(r"\s*[·•]\s*", datetime_text, maxsplit=1)
            if len(parts) == 2:
                date_str = parts[0].strip()
                time_range = parts[1].strip()
                # Extract day name
                m = re.match(r"(\w+),", date_str)
                if m:
                    day_name = m.group(1)
            else:
                date_str = datetime_text

        instructors = []
        seen = set()
        for name_el in ev.select(".instructors .name, .instructor .name"):
            name = name_el.get_text(strip=True)
            if name and name not in seen:
                seen.add(name)
                instructors.append(name)

        results.append({
            "class_name": title,
            "day": day_name,
            "date": date_str,
            "time": time_range,
            "instructors": instructors,
            "mat": MATS[mat_key]["name"],
        })
    return results


async def _fetch_mat(mat_key: str) -> list[dict]:
    url = MATS[mat_key]["url"]
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(url)
        r.raise_for_status()
        return _parse_schedule(r.text, mat_key)


async def _fetch_all() -> list[dict]:
    all_classes = []
    for key in MATS:
        all_classes.extend(await _fetch_mat(key))
    return all_classes


@mcp.tool()
async def get_timetable(mat: str = "all", day: str = "") -> str:
    """Get the London Grapple BJJ timetable for the current week.

    Args:
        mat: Which mat to show: '1' (HQ), '2', or 'all'. Defaults to 'all'.
        day: Filter by day name (e.g. 'Monday'). Defaults to all days.
    """
    if mat == "all":
        classes = await _fetch_all()
    elif mat in MATS:
        classes = await _fetch_mat(mat)
    else:
        return f"Invalid mat '{mat}'. Use '1', '2', or 'all'."

    if day:
        day_lower = day.lower()
        classes = [c for c in classes if c["day"].lower() == day_lower]

    if not classes:
        return "No classes found for the given filters."
    return json.dumps(classes, indent=2)


@mcp.tool()
async def get_classes_today() -> str:
    """Get all BJJ/MMA classes happening today across both mats."""
    today = date.today()
    today_str = today.strftime("%A")  # e.g. "Friday"

    classes = await _fetch_all()
    todays = []
    for c in classes:
        if c["day"].lower() == today_str.lower():
            # Also verify the date matches today (not just day-of-week)
            try:
                parsed = datetime.strptime(c["date"], "%A, %B %d")
                if parsed.month == today.month and parsed.day == today.day:
                    todays.append(c)
            except ValueError:
                # If date parsing fails, fall back to day-name match
                todays.append(c)

    if not todays:
        return f"No classes found for today ({today_str})."
    return json.dumps(todays, indent=2)


@mcp.tool()
async def search_classes(query: str) -> str:
    """Search classes by name or instructor. Case-insensitive substring match.

    Args:
        query: Search term to match against class names or instructor names.
    """
    classes = await _fetch_all()
    q = query.lower()
    matches = [
        c for c in classes
        if q in c["class_name"].lower()
        or any(q in i.lower() for i in c["instructors"])
    ]
    if not matches:
        return f"No classes found matching '{query}'."
    return json.dumps(matches, indent=2)


if __name__ == "__main__":
    import os
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        port = int(os.environ.get("PORT", "8080"))
        mcp.run(transport="sse")
    else:
        mcp.run()
