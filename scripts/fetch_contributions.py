"""Descarga el calendario público de contribuciones de un usuario de GitHub.

No usa tokens: lee el HTML público https://github.com/users/<user>/contributions.
Salida: data/contributions.json (días, totales y rachas).
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "Skaiiner"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch_days():
    r = requests.get(URL, headers={"User-Agent": "profile-readme-bot"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # El recuento exacto de cada día viene en un <tool-tip for="id-de-la-celda">.
    counts = {}
    for tip in soup.find_all("tool-tip"):
        m = re.match(r"\s*(No|\d+)\s+contributions?\b", tip.get_text())
        if m and tip.get("for"):
            counts[tip["for"]] = 0 if m.group(1) == "No" else int(m.group(1))

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        d = td.get("data-date")
        if not d or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            continue
        level = int(td.get("data-level", "0"))
        if not 0 <= level <= 4:
            raise ValueError(f"nivel inesperado {level} en {d}")
        days.append({"date": d, "count": counts.get(td.get("id"), 0), "level": level})

    days.sort(key=lambda x: x["date"])
    if not 300 <= len(days) <= 380:
        raise ValueError(f"se esperaban ~365 días y llegaron {len(days)}: ¿cambió el HTML de GitHub?")
    return days


def streaks(days):
    by_date = {date.fromisoformat(d["date"]): d["count"] for d in days}
    today = max(by_date)
    longest = run = 0
    cur = date.min
    for d in sorted(by_date):
        if by_date[d] > 0:
            run = run + 1 if (d - cur) == timedelta(days=1) else 1
            cur = d
            longest = max(longest, run)
    # Racha actual: hoy aún puede estar vacío, así que se empieza desde ayer en ese caso.
    day = today if by_date[today] > 0 else today - timedelta(days=1)
    current = 0
    while by_date.get(day, 0) > 0:
        current += 1
        day -= timedelta(days=1)
    return current, longest


def main():
    days = fetch_days()
    current, longest = streaks(days)
    data = {
        "user": USERNAME,
        "from": days[0]["date"],
        "to": days[-1]["date"],
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"{USERNAME}: {data['total']} contribuciones, racha actual {current}, mejor racha {longest}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # falla en voz alta para que la Action quede en rojo
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
