"""Run every collector, filter, store, and write opportunities.xlsx.

Usage:  python -m tracker.main            (all sources)
        python -m tracker.main --fast     (skip the slow LinkedIn/Indeed scrape)
"""
import os
import sys
import time
from datetime import datetime

from tracker import excel, filters, sources, storage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
XLSX = os.path.join(ROOT, "opportunities.xlsx")


def main():
    fast = "--fast" in sys.argv
    os.makedirs(DATA, exist_ok=True)
    health, collected = [], []

    jobs = dict(sources.COLLECTORS)
    if fast:
        jobs.pop("LinkedIn/Indeed/Google/Naukri")
    jobs["Company career pages (ATS)"] = lambda: sources.ats_feeds(health)

    for name, fn in jobs.items():
        t = time.time()
        try:
            rows = fn()
            kept = [r for r in rows if r["link"] and filters.keep(r)]
            for r in kept:
                r["score"] = filters.score(r)
            collected += kept
            health.append((name, "ok", len(kept), f"{len(rows)} fetched, {len(kept)} matched, {time.time() - t:.0f}s"))
            print(f"  ok   {name:32} {len(kept):5} / {len(rows)}")
        except Exception as e:
            health.append((name, "FAILED", 0, f"{type(e).__name__}: {e}"[:500]))
            print(f"  FAIL {name:32} {type(e).__name__}: {str(e)[:120]}")

    db = storage.connect(os.path.join(DATA, "opportunities.db"))
    new = storage.upsert(db, collected)
    rows = [r for r in storage.active(db) if filters.keep(r)]  # re-filter if config.py changed
    health.insert(0, ("Run", "ok", new, f"{datetime.now():%Y-%m-%d %H:%M} | {new} new | {len(rows)} active"))
    try:
        excel.write(XLSX, rows, health)
    except PermissionError:
        print("!! opportunities.xlsx is open in Excel. Close it and run again.")
        sys.exit(1)
    print(f"\nDone: {new} new today, {len(rows)} active -> {XLSX}")
    _telegram_digest(rows, new)


def _telegram_digest(rows, new):
    """Optional: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to get a daily message."""
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat and new):
        return
    today = datetime.now().strftime("%Y-%m-%d")
    top = sorted((r for r in rows if r["first_seen"] == today), key=lambda r: -int(r["score"] or 0))[:25]
    lines = [f"{new} new opportunities today. Top {len(top)}:"]
    lines += [f"• [{r['type']}] {r['title']} at {r['org'] or r['source']}\n  {r['link']}" for r in top]
    sources.client.post(f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": chat, "text": "\n".join(lines)[:4000],
                              "disable_web_page_preview": True})


if __name__ == "__main__":
    main()
