# Opportunity Tracker: Research Notes

Goal: one Excel sheet, refreshed every day without me doing anything, that lists every new **job, internship, hackathon and contest** from career pages, job boards, hackathon platforms and social media. It should cost nothing.

---

## 1. How job listings actually get published

Almost no company builds its own careers page from scratch. They pay an **Applicant Tracking System (ATS)**, and the ATS hosts the listings. Most ATSs expose a **public, unauthenticated JSON feed** for every company that uses them. That is the main insight of this research:

> Instead of scraping 10,000 different career pages, query about 8 ATS APIs with a list of company slugs.

| ATS | Public endpoint (no key) | Who uses it |
|---|---|---|
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/{company}/jobs` | Most US/EU tech startups |
| Lever | `https://api.lever.co/v0/postings/{company}?mode=json` | Startups |
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/{company}` | Newer startups (YC, AI labs) |
| Workable | `https://apply.workable.com/api/v1/widget/accounts/{company}` | SMBs |
| SmartRecruiters | `https://api.smartrecruiters.com/v1/companies/{company}/postings` | Large enterprises |
| Recruitee | `https://{company}.recruitee.com/api/offers/` | EU SMBs |
| Workday | `https://{co}.wd{N}.myworkdayjobs.com/wday/cxs/{co}/{site}/jobs` (POST) | Fortune 500 |
| BambooHR / Breezy / Teamtailor / Personio | Per-company JSON or XML feeds | SMBs |

**Finding the company slugs:** search engines (`site:boards.greenhouse.io`, `site:jobs.lever.co`, `site:jobs.ashbyhq.com`), Common Crawl, and open-source lists on GitHub. People have published lists with tens of thousands of slugs. One harvest gives coverage of most tech hiring.

Companies with no ATS (small startups, Indian SMEs) post on job boards, LinkedIn, X, or Telegram. They are covered by the sources below.

---

## 2. Source catalogue, ranked by value ÷ effort

### A. Free APIs and feeds (reliable, legal, easy)
| Source | Covers | Access |
|---|---|---|
| ATS feeds (above) | Jobs + internships at about 50k companies | JSON, free |
| **python-jobspy** (open-source library) | LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter, Naukri | Scrapes them for you; rate-limited, so go gently |
| HN "Who is Hiring" (monthly) | Startup jobs | Algolia HN API, free |
| RemoteOK, Remotive, Arbeitnow, Himalayas, WeWorkRemotely | Remote jobs | Free JSON/RSS |
| Adzuna, USAJobs, The Muse, Jooble | Aggregated jobs | Free API key |
| GitHub repos: SimplifyJobs *Summer-Internships* / *New-Grad-Positions*, and similar | Internships + new-grad, curated daily | Parse README/JSON from the raw GitHub file |
| Reddit (`r/forhire`, `r/internships`, `r/hackathons`, `r/developersIndia` …) | Mixed | Append `.json` to any subreddit URL |
| **CLIST.by API** | Aggregates about 200 contest sites (Codeforces, LeetCode, AtCoder, CodeChef, Kaggle, HackerRank, TopCoder…) | Free API key: one source covers almost all coding contests |
| Codeforces / Kaggle APIs | Contests, competitions | Free |

### B. Hackathon and challenge platforms (scrape their internal JSON)
These sites load listings through internal JSON calls that you can see in the browser's Network tab. Calling those directly beats parsing HTML.
- **Devpost**: `devpost.com/api/hackathons?status[]=upcoming&status[]=open`
- **MLH**: season page `mlh.io/seasons/2027/events`
- **Devfolio**: Indian and Web3 hackathons
- **Unstop** (formerly Dare2Compete): the biggest Indian source for hackathons, quizzes, case competitions and internships. Has a public search JSON API.
- **HackerEarth** challenges, **Hack2Skill**, **Lu.ma** (event search by "hackathon"), **Eventbrite**, **DoraHacks**, **ETHGlobal**, **Gitcoin**, **Kaggle**, **DrivenData**, **Zindi**, **AIcrowd**, **Topcoder**, **Superteam Earn** (bounties)
- **Internshala** (Indian internships), **Wellfound** (startups; harder to scrape), **Naukri**/**Foundit** (via JobSpy or their JSON)

### C. Social media (where the "smallest" opportunities appear)
| Platform | Reality in 2026 | Free approach |
|---|---|---|
| **X / Twitter** | Official API has no useful free read tier; Nitter is mostly dead | (1) Google/Bing search with `site:x.com "hackathon" "register"`; (2) RSS bridges (RSSHub) for specific accounts; (3) a headless browser logged into your own account, run slowly. Expect this to be the most fragile source. |
| **YouTube** | Data API v3 has a free quota (10,000 units/day ≈ 100 searches) | Search "hiring", "internship", "hackathon" ordered by date; channel RSS feeds (`youtube.com/feeds/videos.xml?channel_id=…`) are free and unlimited |
| **LinkedIn posts** | Aggressive anti-scraping | JobSpy for job listings; posts are a "maybe later" with a logged-in headless browser |
| **Telegram** | Huge for Indian off-campus drives and internships | **Telethon** (free API ID from my.telegram.org) reads public channels; very reliable |
| **Discord** | Many hackathon announcements | A bot can only read servers you join; optional |
| **Google Search / Google Jobs** | Catches anything on a company's own site | SerpAPI (100 free/mo), Google Programmable Search (100/day free), or DuckDuckGo via `duckduckgo-search` lib |

### D. Long tail: company websites with no ATS
- Keep a list of URLs (college fests, GDG/MLSA chapters, startup careers pages). Fetch each daily, **hash the content, and diff it**. When the page changes, send the new text to an LLM to extract opportunities.
- Tools: `changedetection.io` (self-hosted, free) or a 30-line Python script.

---

## 3. Making messy text structured: a free LLM

Social posts and changed web pages are free text. An LLM turns them into rows:
`{type, title, org, location, remote, deadline, stipend/salary, eligibility, link}`.

| Option | Cost | Notes |
|---|---|---|
| **Ollama** + Llama 3.x / Qwen / Gemma (local) | Free, offline | Needs about 8 GB RAM; fine for classification and extraction |
| Google Gemini free tier | Free | High daily limits; fast |
| Groq free tier | Free | Very fast Llama models |
| OpenRouter free models | Free | Fallback |

Structured APIs (ATS, Devpost, CLIST) **don't need an LLM**. Use one only for messy sources, which keeps it well inside free limits.

**Reaching "every listing" without drowning:** collect everything, then filter by profile (skills, location, grad year, remote) and score relevance. The Excel file keeps everything, with a "Match score" column and filters.

---

## 4. Proposed system design

```
          ┌────────────── Scheduler (daily, or every 6h) ───────────────┐
          │  GitHub Actions cron (free, runs without my PC)             │
          │  or Windows Task Scheduler (works offline-ish / local LLM)   │
          └──────────────────────────────┬──────────────────────────────┘
                                         ▼
 ┌──────────── Collectors (one small plugin per source) ─────────────┐
 │ ATS feeds │ JobSpy │ Devpost/MLH/Unstop/Devfolio │ CLIST │ GitHub │
 │ Reddit │ YouTube RSS │ Telegram │ X (search/RSS) │ Page-diff     │
 └──────────────────────────────┬────────────────────────────────────┘
                                ▼
          Normalise → LLM extract (only for free text) → Classify
          (job / internship / hackathon / contest / bounty)
                                ▼
          Dedupe (URL + fuzzy title/org match) → SQLite (history)
                                ▼
          Filter + score against my profile (skills, location, year)
                                ▼
 ┌──────────────────────── Outputs ───────────────────────────┐
 │ opportunities.xlsx: tabs: NEW TODAY │ Jobs │ Internships │  │
 │   Hackathons │ Contests │ Closing soon │ All               │
 │ Optional: Google Sheet, Telegram/Email daily digest,       │
 │   one-click "Refresh now" desktop shortcut                 │
 └────────────────────────────────────────────────────────────┘
```

**Excel columns:** Date found · Type · Title · Organisation · Location · Remote · Deadline · Days left · Stipend/Salary · Eligibility · Source · Link · Match score · Status (dropdown: New/Applied/Skipped).

**Zero-click mode:** GitHub Actions runs daily → commits `opportunities.xlsx` → pushes a Telegram message with the top new items. Or locally: Task Scheduler runs at login, and the file is always fresh when you open it.

**Offline:** collecting needs the internet by definition. "Offline" here means the LLM and Excel run locally (Ollama) with no paid cloud, and the sheet is readable anytime.

**Stack:** Python 3.12, `httpx`, `python-jobspy`, `playwright` (only for JS-heavy sites), `telethon`, `feedparser`, `rapidfuzz` (dedupe), `sqlite3`, `openpyxl`, `ollama`/Gemini SDK.

---

## 5. Honest limits
- **"Every opportunity" isn't 100 % reachable.** Private Discord/WhatsApp groups and closed LinkedIn posts can't be read reliably. A realistic target is **about 90 %+ of public listings**, much more than any single site gives.
- **Terms of service:** LinkedIn, Indeed and X forbid scraping. Use official/public APIs first, keep request rates low, and use the tracker only personally.
- **Breakage:** scrapers break when sites change. The plugin design isolates failures, and a daily "source health" tab shows which collector failed.
- **Some API paths above are from memory.** Each one gets verified while its collector is built.

---

## 6. Build roadmap
1. **MVP (1 session):** ATS feeds + JobSpy + Devpost + Unstop + CLIST + SimplifyJobs → SQLite → Excel. Daily via Task Scheduler.
2. Profile-based filtering and match score; "NEW TODAY" and "Closing soon" tabs.
3. Telegram channels + Reddit + YouTube RSS + Lu.ma/Devfolio/MLH.
4. LLM extraction (Ollama/Gemini) + page-diff watcher for custom URLs.
5. X/Twitter via search + RSS bridges; move to GitHub Actions; Telegram digest bot.

## 7. Inputs I need from the user
- Target roles/skills, location(s) / remote preference, graduation year, country (India-specific sources?)
- Does the PC stay on daily, or should it run in the cloud (GitHub account)?
- Optional free keys: Gemini or Groq, YouTube Data API, Telegram API ID, CLIST, Adzuna
- Any specific companies, Telegram channels, colleges or communities to always watch
