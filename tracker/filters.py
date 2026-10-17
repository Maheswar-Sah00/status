"""Decide which collected rows match the profile in config.py, and score them."""
import re

import config


def _has(text, words):
    t = f" {text.lower()} "
    return any(w in t for w in words)


def location_ok(o):
    loc = o["location"]
    if not loc:
        # Indian portals often omit location; global boards without one are unknown -> keep.
        return True
    if _has(loc, config.INDIA_KEYWORDS):
        return True
    if not _has(loc, config.REMOTE_KEYWORDS):
        return False
    # "Remote" only counts if no other place is named ("Remote - US" is not open to India).
    rest = loc.lower()
    for w in config.REMOTE_KEYWORDS + ["only", "in", "from", "/", "-"]:
        rest = rest.replace(w, " ")
    return not re.search(r"[a-z]{2,}", rest)


def keep(o):
    if o["type"] in ("Hackathon", "Contest"):
        if o["source"] == "Unstop" and o["type"] == "Contest" and not _has(
                o["title"], config.ROLE_KEYWORDS + config.CONTEST_KEYWORDS):
            return False
        # In-person events abroad are not reachable; online or India ones are.
        return o["source"] in ("Codeforces", "CodeChef", "LeetCode", "CLIST") or location_ok(o)
    title = o["title"]
    if not _has(title, config.ROLE_KEYWORDS) or _has(title, config.EXCLUDE_KEYWORDS):
        return False
    if config.SENIOR_KEYWORDS and _has(title, config.SENIOR_KEYWORDS):
        return False
    return location_ok(o)


def score(o):
    """0-100: higher = more relevant to a CSE student/fresher in India or remote."""
    s = 50
    t, loc = o["title"].lower(), o["location"].lower()
    if o["type"] == "Internship":
        s += 15
    if re.search(r"\b(intern|fresher|graduate|entry|junior|jr|trainee|new grad|associate|sde[- ]?1|i)\b", t):
        s += 15
    if re.search(r"software|sde|swe|developer|full stack|backend|frontend|machine learning|data", t):
        s += 10
    if _has(loc, config.INDIA_KEYWORDS):
        s += 5
    if _has(loc, config.REMOTE_KEYWORDS):
        s += 5
    if o["type"] in ("Hackathon", "Contest"):
        s = 70 + (10 if _has(loc, ["online", "india"]) else 0)
    return min(s, 100)
