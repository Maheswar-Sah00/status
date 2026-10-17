"""One collector function per source. Each returns a list of Opportunity dicts.

A collector may raise; main.py catches it and records it on the health tab.
"""
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

import config

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
client = httpx.Client(headers={"User-Agent": UA, "Accept": "application/json, text/html"},
                      timeout=30, follow_redirects=True)


def opp(type_, title, org, link, source, location="", deadline="", posted="",
        pay="", notes=""):
    return {
        "type": type_, "title": (title or "").strip(), "org": (org or "").strip(),
        "location": (location or "").strip(), "deadline": _date(deadline),
        "posted": _date(posted), "pay": (pay or "").strip(), "source": source,
        "link": link, "notes": (notes or "").strip(),
    }


def _date(v):
    """Normalise ISO strings / epoch seconds / epoch ms to YYYY-MM-DD."""
    if not v:
        return ""
    try:
        if isinstance(v, (int, float)):
            v = v / 1000 if v > 1e11 else v
            return datetime.fromtimestamp(v, timezone.utc).strftime("%Y-%m-%d")
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return str(v)[:10] if re.match(r"\d{4}-\d{2}-\d{2}", str(v)) else ""


def _job_type(title):
    return "Internship" if re.search(r"\bintern", title, re.I) else "Job"


def _strip(s):
    return re.sub(r"<[^>]+>", "", html.unescape(s or "")).strip()


# ---------------------------------------------------------------- ATS feeds

def _greenhouse(slug):
    data = client.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs").json()
    return [opp(_job_type(j["title"]), j["title"], slug, j["absolute_url"], "Greenhouse",
                (j.get("location") or {}).get("name", ""),
                posted=j.get("first_published") or j.get("updated_at"))
            for j in data.get("jobs", [])]


def _lever(slug):
    data = client.get(f"https://api.lever.co/v0/postings/{slug}?mode=json").json()
    if not isinstance(data, list):
        raise ValueError("not a Lever board")
    out = []
    for j in data:
        c = j.get("categories") or {}
        loc = ", ".join(c.get("allLocations") or [c.get("location") or ""])
        if j.get("workplaceType") == "remote":
            loc += " (Remote)"
        t = "Internship" if "intern" in (c.get("commitment") or "").lower() else _job_type(j["text"])
        out.append(opp(t, j["text"], slug, j["hostedUrl"], "Lever", loc, posted=j.get("createdAt")))
    return out


def _ashby(slug):
    data = client.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}").json()
    out = []
    for j in data.get("jobs", []):
        locs = [j.get("location") or ""] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
        loc = ", ".join(l for l in locs if l) + (" (Remote)" if j.get("isRemote") else "")
        t = "Internship" if j.get("employmentType") == "Intern" else _job_type(j["title"])
        out.append(opp(t, j["title"], slug, j["jobUrl"], "Ashby", loc, posted=j.get("publishedAt")))
    return out


def ats_feeds(health):
    """Fetch every configured company in parallel; per-company failures go to health."""
    tasks = ([(_greenhouse, s) for s in config.GREENHOUSE] +
             [(_lever, s) for s in config.LEVER] +
             [(_ashby, s) for s in config.ASHBY])

    def run(t):
        fn, slug = t
        try:
            return fn(slug), None
        except Exception as e:
            return [], f"{fn.__name__[1:]}:{slug} ({type(e).__name__})"

    out, bad = [], []
    with ThreadPoolExecutor(16) as ex:
        for rows, err in ex.map(run, tasks):
            out += rows
            if err:
                bad.append(err)
    if bad:
        health.append(("ATS (skipped boards)", "warn", len(bad), "; ".join(bad)))
    return out


# ------------------------------------------------- LinkedIn/Indeed/Google/Naukri

def jobspy_boards():
    from jobspy import scrape_jobs  # heavy import, keep local

    out = []
    for term in config.JOB_SEARCH_TERMS:
        for remote in (False, True):
            try:
                df = scrape_jobs(
                    site_name=["linkedin", "indeed", "google", "naukri"],
                    search_term=term, google_search_term=f"{term} jobs in India since yesterday",
                    location="India", country_indeed="India", is_remote=remote,
                    results_wanted=30, hours_old=config.JOB_SEARCH_HOURS_OLD,
                    verbose=0,
                )
            except Exception:
                continue
            for r in df.fillna("").to_dict("records"):
                pay = ""
                if r.get("min_amount"):
                    pay = f"{r.get('currency', '')} {r['min_amount']}-{r.get('max_amount', '')} /{r.get('interval', '')}"
                loc = str(r.get("location", "")) + (" (Remote)" if r.get("is_remote") is True else "")
                out.append(opp(_job_type(r["title"]), r["title"], r.get("company", ""),
                               r.get("job_url"), f"JobSpy/{r.get('site', '')}", loc,
                               posted=str(r.get("date_posted") or ""), pay=pay))
    return out


# -------------------------------------------------------------- Indian portals

def unstop():
    out = []
    kinds = {"hackathons": "Hackathon", "competitions": "Contest",
             "internships": "Internship", "jobs": "Job"}
    for kind, t in kinds.items():
        for page in range(1, 11):
            d = client.get("https://unstop.com/api/public/opportunity/search-result",
                           params={"opportunity": kind, "per_page": 30, "oppstatus": "open",
                                   "page": page}).json()["data"]
            for x in d["data"]:
                jd = x.get("jobDetail") or {}
                locs = [l.get("city", "") if isinstance(l, dict) else str(l) for l in jd.get("locations") or []]
                loc = ", ".join(filter(None, locs)) or x.get("region", "")
                if jd.get("type") == "wfh":
                    loc = (loc + " Remote").strip()
                pay = ""
                if jd.get("max_salary"):
                    pay = f"INR {jd.get('min_salary') or ''}-{jd['max_salary']} /{jd.get('pay_in', '')}"
                elif x.get("prizes"):
                    total = sum((p.get("cash") or 0) for p in x["prizes"] if isinstance(p, dict))
                    pay = f"Prizes INR {total:,}" if total else ""
                out.append(opp(t, x["title"], (x.get("organisation") or {}).get("name", ""),
                               "https://unstop.com/" + x["public_url"], "Unstop",
                               loc or "India", deadline=x.get("end_date"),
                               posted=x.get("approved_date") or x.get("updated_at"), pay=pay))
            if page >= d.get("last_page", 1):
                break
    return out


def internshala():
    out = []
    pages = [
        ("internships", "computer-science-internship"),
        ("internships", "software-development-internship"),
        ("internships", "web-development-internship"),
        ("internships", "python-django-internship"),
        ("internships", "machine-learning-internship"),
        ("internships", "data-science-internship"),
        ("internships", "work-from-home-computer-science-internships"),
        ("jobs", "software-development-jobs"),
        ("jobs", "fresher-jobs"),
    ]
    for kind, slug in pages:
        soup = BeautifulSoup(client.get(f"https://internshala.com/{kind}/{slug}/").text, "html.parser")
        for card in soup.select("div.individual_internship[data-href]"):
            a = card.select_one(".job-title-href") or card.select_one("h2 a, h3 a")
            if not a:
                continue
            org = card.select_one(".company-name")
            loc = card.select_one(".locations")
            pay = card.select_one(".stipend") or card.select_one(".desktop")
            t = "Internship" if card.get("employment_type") == "internship" else "Job"
            out.append(opp(t, a.get_text(" ", strip=True), org.get_text(strip=True) if org else "",
                           "https://internshala.com" + card["data-href"], "Internshala",
                           loc.get_text(" ", strip=True) if loc else "India",
                           pay=pay.get_text(" ", strip=True) if pay else ""))
    return out


# ------------------------------------------------------------------ hackathons

def devpost():
    out = []
    for page in range(1, 16):
        hs = client.get("https://devpost.com/api/hackathons",
                        params={"status[]": ["upcoming", "open"], "page": page}).json()["hackathons"]
        if not hs:
            break
        for h in hs:
            dates = h.get("submission_period_dates", "")
            out.append(opp("Hackathon", h["title"], h.get("organization_name", ""), h["url"],
                           "Devpost", (h.get("displayed_location") or {}).get("location", ""),
                           deadline=_devpost_end(dates), pay=_strip(h.get("prize_amount")),
                           notes=f"{dates} | " + ", ".join(t["name"] for t in h.get("themes", []))))
    return out


def _devpost_end(s):
    """'Aug 31 - Oct 23, 2026' or 'Oct 01 - 23, 2026' -> '2026-10-23'."""
    m = re.search(r"-\s*(?:([A-Za-z]{3})\s+)?(\d{1,2}),\s*(\d{4})", s or "")
    if not m:
        return ""
    mon = m.group(1) or re.match(r"[A-Za-z]{3}", s).group(0)
    try:
        return datetime.strptime(f"{mon} {m.group(2)} {m.group(3)}", "%b %d %Y").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def devfolio():
    out = []
    for status in ("application_open", "upcoming"):
        hits = client.post("https://api.devfolio.co/api/search/hackathons",
                           json={"type": status, "from": 0, "size": 100}).json()["hits"]["hits"]
        for h in (x["_source"] for x in hits):
            s = h.get("hackathon_setting") or {}
            loc = "Online" if h.get("is_online") else ", ".join(filter(None, [h.get("city"), h.get("country")]))
            out.append(opp("Hackathon", h["name"], "", f"https://{h['slug']}.devfolio.co/",
                           "Devfolio", loc or "India", deadline=s.get("reg_ends_at"),
                           notes=f"Runs {_date(h.get('starts_at'))} to {_date(h.get('ends_at'))}"))
    return out


def mlh():
    year = datetime.now().year + (1 if datetime.now().month >= 7 else 0)
    page = client.get(f"https://mlh.io/seasons/{year}/events").text
    raw = re.search(r'<script data-page="app" type="application/json">(.*?)</script>', page, re.S)
    events = json.loads(raw.group(1))["props"].get("upcomingEvents", [])
    out = []
    for e in events:
        fmt = e.get("formatType", "")
        loc = "Online" if fmt == "digital" else f"{e.get('location', '')} ({fmt})"
        out.append(opp("Hackathon", e["name"], "MLH", e.get("websiteUrl") or "https://mlh.io" + e["url"],
                       "MLH", loc, deadline=e.get("startsAt"),
                       notes=f"{e.get('dateRange', '')} | {e.get('region', '')}"))
    return out


# -------------------------------------------------------------------- contests

def codeforces():
    rows = client.get("https://codeforces.com/api/contest.list").json()["result"]
    return [opp("Contest", c["name"], "Codeforces", f"https://codeforces.com/contests/{c['id']}",
                "Codeforces", "Online", deadline=c["startTimeSeconds"],
                notes=f"Starts {datetime.fromtimestamp(c['startTimeSeconds'], timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30))):%d %b %H:%M} IST")
            for c in rows if c["phase"] == "BEFORE"]


def codechef():
    d = client.get("https://www.codechef.com/api/list/contests/all").json()
    return [opp("Contest", c["contest_name"], "CodeChef",
                f"https://www.codechef.com/{c['contest_code']}", "CodeChef", "Online",
                deadline=c.get("contest_start_date_iso"),
                notes=f"Starts {c.get('contest_start_date', '')} IST")
            for c in d.get("future_contests", [])]


def leetcode():
    q = "{ upcomingContests { title titleSlug startTime } }"
    d = client.post("https://leetcode.com/graphql", json={"query": q},
                    headers={"Referer": "https://leetcode.com/contest/"}).json()
    return [opp("Contest", c["title"], "LeetCode", f"https://leetcode.com/contest/{c['titleSlug']}",
                "LeetCode", "Online", deadline=c["startTime"])
            for c in d["data"]["upcomingContests"]]


def kaggle_and_more_via_clist():
    """CLIST covers ~200 contest sites. Needs free CLIST_USERNAME + CLIST_API_KEY env vars."""
    import os
    user, key = os.environ.get("CLIST_USERNAME"), os.environ.get("CLIST_API_KEY")
    if not (user and key):
        return []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    d = client.get("https://clist.by/api/v4/contest/",
                   params={"upcoming": "true", "start__gt": now, "limit": 300, "order_by": "start"},
                   headers={"Authorization": f"ApiKey {user}:{key}"}).json()
    return [opp("Contest", c["event"], c["host"], c["href"], "CLIST", "Online", deadline=c["start"])
            for c in d.get("objects", [])]


# --------------------------------------------------------------- remote / misc

def simplify():
    out = []
    for repo, t in (("Summer2026-Internships", "Internship"), ("New-Grad-Positions", "Job")):
        rows = client.get(f"https://raw.githubusercontent.com/SimplifyJobs/{repo}/dev/.github/scripts/listings.json").json()
        cutoff = (datetime.now() - timedelta(days=30)).timestamp()
        for r in rows:
            if r.get("active") and r.get("is_visible", True) and r.get("date_posted", 0) > cutoff:
                out.append(opp(t, r["title"], r["company_name"], r["url"], "SimplifyJobs (GitHub)",
                               ", ".join(r.get("locations") or []), posted=r["date_posted"]))
    return out


def remoteok():
    rows = client.get("https://remoteok.com/api").json()[1:]
    return [opp(_job_type(r.get("position", "")), r.get("position"), r.get("company"), r.get("url"),
                "RemoteOK", (r.get("location") or "Worldwide") + " (Remote)", posted=r.get("date"),
                pay=f"USD {r['salary_min']}-{r.get('salary_max', '')}" if r.get("salary_min") else "")
            for r in rows if r.get("position")]


def remotive():
    rows = client.get("https://remotive.com/api/remote-jobs", params={"category": "software-dev"}).json()["jobs"]
    return [opp(_job_type(r["title"]), r["title"], r["company_name"], r["url"], "Remotive",
                (r.get("candidate_required_location") or "") + " (Remote)",
                posted=r.get("publication_date"), pay=r.get("salary", ""))
            for r in rows]


# name -> function. main.py runs every entry.
COLLECTORS = {
    "Unstop": unstop,
    "Internshala": internshala,
    "LinkedIn/Indeed/Google/Naukri": jobspy_boards,
    "Devpost": devpost,
    "Devfolio": devfolio,
    "MLH": mlh,
    "Codeforces": codeforces,
    "CodeChef": codechef,
    "LeetCode": leetcode,
    "CLIST (optional key)": kaggle_and_more_via_clist,
    "SimplifyJobs": simplify,
    "RemoteOK": remoteok,
    "Remotive": remotive,
}
