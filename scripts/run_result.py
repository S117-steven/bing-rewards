# -*- coding: utf-8 -*-
"""Shared result and Rewards Daily Set parsing helpers.

The two browser workers are launched as independent processes.  They therefore
emit one machine-readable result line which the manager can consume without
having to infer success from human-readable log messages.
"""

from __future__ import annotations

import json
import re
from datetime import datetime


RESULT_PREFIX = "__BING_REWARDS_RESULT__ "


# React Server Components data is escaped in the page source used by the
# current Rewards dashboard.  Keep a plain-JSON variant as a fallback because
# the same data is not escaped in every Edge/Selenium page-source version.
_REACT_PATTERNS = (
    re.compile(
        r'\\"date\\":\\"(?P<date>.*?)\\",\\"description\\":\\"(?P<description>.*?)'
        r'\\",\\"destination\\":\\"(?P<destination>.*?)\\",\\"hash\\":.*?'
        r'\\",\\"isCompleted\\":(?P<completed>true|false).*?,\\"offerId\\":\\"'
        r'(?P<offer>Global_DailySet_[0-9]+_Child[0-9]+)\\",'
        r'\\"points\\":(?P<points>[0-9]+),\\"title\\":\\"(?P<title>.*?)\\"',
        re.DOTALL,
    ),
    re.compile(
        r'"date"\s*:\s*"(?P<date>.*?)"\s*,\s*"description"\s*:\s*"(?P<description>.*?)'
        r'"\s*,\s*"destination"\s*:\s*"(?P<destination>.*?)"\s*,\s*"hash"\s*:.*?'
        r'"isCompleted"\s*:\s*(?P<completed>true|false).*?,\s*'
        r'"offerId"\s*:\s*"(?P<offer>Global_DailySet_[0-9]+_Child[0-9]+)"\s*,'
        r'"points"\s*:\s*(?P<points>[0-9]+)\s*,\s*"title"\s*:\s*"(?P<title>.*?)"',
        re.DOTALL,
    ),
)


def _decode_rsc_value(value: str) -> str:
    try:
        return json.loads('"' + value + '"')
    except Exception:
        return value.replace(r"\u0026", "&").replace(r'\"', '"')


def extract_react_daily_set_state(source: str, today: str | None = None):
    """Return the current day's Daily Set state, or ``None`` if not parsed.

    The return value contains all records, including completed records.  That
    distinction is important: an empty pending list can mean either that all
    tasks are already complete or that the page parser failed.
    """

    today = today or datetime.now().strftime("%m/%d/%Y")
    matches = []
    for pattern in _REACT_PATTERNS:
        matches = [match for match in pattern.finditer(source or "")
                   if match.group("date") == today]
        if matches:
            break

    if not matches:
        return None

    by_offer = {}
    for match in matches:
        offer_id = match.group("offer")
        task = {
            "href": _decode_rsc_value(match.group("destination")),
            "text": _decode_rsc_value(match.group("title")),
            "offer_id": offer_id,
            "points": int(match.group("points")),
            "completed": match.group("completed") == "true",
        }
        if not task["href"] or not task["text"]:
            continue

        # The RSC payload can contain a record more than once.  If either copy
        # says completed, keep that fact instead of reintroducing a false
        # pending task.
        previous = by_offer.get(offer_id)
        if previous is None or task["completed"]:
            by_offer[offer_id] = task

    tasks = list(by_offer.values())
    if not tasks:
        # A matching date with no usable task records is a parser failure, not
        # evidence that the account has already completed everything.
        return None
    pending_tasks = [task for task in tasks if not task["completed"]]
    completed_tasks = [task for task in tasks if task["completed"]]
    return {
        "date": today,
        "total": len(tasks),
        "completed": len(completed_tasks),
        "pending": len(pending_tasks),
        "tasks": tasks,
        "pending_tasks": pending_tasks,
    }


def emit_result(result: dict) -> None:
    """Emit the one-line result consumed by ``manager.pyw``."""

    print(
        RESULT_PREFIX + json.dumps(result, ensure_ascii=False, separators=(",", ":")),
        flush=True,
    )


def parse_result_line(line: str):
    """Parse a worker result line; return ``None`` for normal log lines."""

    if not line.startswith(RESULT_PREFIX):
        return None
    try:
        value = json.loads(line[len(RESULT_PREFIX):])
    except (TypeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None
