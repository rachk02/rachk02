"""Recupere le calendrier de contributions et ecrit data/contributions.json.

Usage : python scripts/fetch_contributions.py
Jeton : GITHUB_TOKEN / GH_TOKEN dans l'environnement, sinon `gh auth token`.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from config import PERSON  # noqa: E402

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def token() -> str:
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(key)
        if value:
            return value.strip()
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except Exception as exc:  # pragma: no cover
        raise SystemExit("Aucun jeton GitHub disponible.") from exc


def fetch(login: str, auth: str) -> dict:
    payload = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {auth}",
            "Content-Type": "application/json",
            "User-Agent": f"{login}-readme-cards",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.load(response)
    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]["user"]


def streaks(days: list[tuple[dt.date, int]]) -> tuple[int, int, int]:
    counts = {day: count for day, count in days}
    longest = current = 0
    for day, count in days:
        if count > 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    last = max(counts) if counts else dt.date.today()
    cursor = last
    if counts.get(cursor, 0) == 0:
        cursor -= dt.timedelta(days=1)
    run = 0
    while counts.get(cursor, 0) > 0:
        run += 1
        cursor -= dt.timedelta(days=1)
    return run, longest, sum(1 for _, count in days if count > 0)


MONTHS_FR = [
    "JAN",
    "FÉV",
    "MAR",
    "AVR",
    "MAI",
    "JUIN",
    "JUIL",
    "AOÛ",
    "SEP",
    "OCT",
    "NOV",
    "DÉC",
]


def main() -> None:
    user = fetch(PERSON["login"], token())
    collection = user["contributionsCollection"]
    calendar = collection["contributionCalendar"]

    days: list[tuple[dt.date, int]] = []
    for week in calendar["weeks"]:
        for item in week["contributionDays"]:
            days.append((dt.date.fromisoformat(item["date"]), item["contributionCount"]))
    days.sort()

    current, longest, active = streaks(days)
    busiest_day, busiest_count = max(days, key=lambda pair: (pair[1], -pair[0].toordinal()))

    months: list[dict] = []
    for day, count in days:
        key = f"{day.year}-{day.month:02d}"
        if not months or months[-1]["key"] != key:
            months.append(
                {
                    "key": key,
                    "label": MONTHS_FR[day.month - 1],
                    "year": day.year,
                    "total": 0,
                }
            )
        months[-1]["total"] += count
    months = months[-12:]

    data = {
        "login": PERSON["login"],
        "generated_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "created_at": user["createdAt"],
        "total": calendar["totalContributions"],
        "commits": collection["totalCommitContributions"],
        "pull_requests": collection["totalPullRequestContributions"],
        "issues": collection["totalIssueContributions"],
        "current_streak": current,
        "longest_streak": longest,
        "active_days": active,
        "busiest_day": busiest_day.isoformat(),
        "busiest_count": busiest_count,
        "months": months,
        "days": [{"date": day.isoformat(), "count": count} for day, count in days],
        "weeks": [
            [
                {"date": item["date"], "count": item["contributionCount"]}
                for item in week["contributionDays"]
            ]
            for week in calendar["weeks"]
        ],
    }

    out = ROOT / "data" / "contributions.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{out.relative_to(ROOT)} : {data['total']} contributions, serie {current}, record {longest}")


if __name__ == "__main__":
    main()

