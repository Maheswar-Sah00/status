"""Your profile. Edit this file to change what lands in the sheet."""

# A job/internship title must contain at least one of these (lowercase match).
ROLE_KEYWORDS = [
    "software", "developer", "sde", "swe", "engineer", "programmer", "coder",
    "backend", "back-end", "back end", "frontend", "front-end", "front end",
    "full stack", "fullstack", "full-stack", "web", "mobile", "android", "ios",
    "flutter", "react", "node", "python", "java", "golang", "rust", "c++", ".net",
    "data scien", "data engineer", "data analyst", "machine learning", "ml ", "ai ",
    "artificial intelligence", "deep learning", "nlp", "computer vision", "llm",
    "devops", "cloud", "sre", "site reliability", "platform", "infrastructure",
    "qa", "test", "automation", "security", "cyber", "blockchain", "web3",
    "embedded", "firmware", "game", "computer science", "cse", "it ", "technology",
]

# ...but not if it contains any of these (non-CS "engineer" roles, sales etc).
EXCLUDE_KEYWORDS = [
    "mechanical", "civil", "electrical engineer", "chemical", "sales", "marketing",
    "business development", "recruit", "hr ", "human resource", "accountant",
    "finance", "legal", "content writ", "graphic design", "customer support",
    "telecaller", "field", "site engineer", "service engineer", "hvac", "piping",
    "account executive", "customer success", "video creator", "consultant",
]

# Unstop "competitions" are mostly non-tech quizzes; keep only ones whose title
# matches ROLE_KEYWORDS or one of these. Hackathons are always kept.
CONTEST_KEYWORDS = [
    "code", "coding", "hack", "ctf", "capture the flag", "tech", "program",
    "algorithm", " ai", "data", "robot", "app", "dev", "build", "innovation",
    "ideathon", "startup", "design challenge",
]

# Seniority you are NOT eligible for. Set to [] to keep everything.
SENIOR_KEYWORDS = [
    "senior", "sr.", "sr ", "staff", "principal", "lead", "manager", "director",
    "head of", "architect", "vp ", "vice president", "iii", " iv",
]

# A listing's location must match one of these (or be remote/online).
INDIA_KEYWORDS = [
    "india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "chennai",
    "delhi", "gurgaon", "gurugram", "noida", "kolkata", "ahmedabad", "kochi",
    "trivandrum", "thiruvananthapuram", "jaipur", "indore", "chandigarh",
    "coimbatore", "mysore", "mysuru", "bhubaneswar", "nagpur", "vizag",
    "visakhapatnam", "lucknow", "surat", "vadodara", "goa",
]
REMOTE_KEYWORDS = [
    "remote", "anywhere", "worldwide", "work from home", "wfh", "online",
    "global", "apac", "asia", "virtual", "distributed",
]

# Search terms used against LinkedIn / Indeed / Google Jobs / Naukri.
JOB_SEARCH_TERMS = [
    "software engineer intern",
    "software developer fresher",
    "SDE intern",
    "software engineer entry level",
    "full stack developer intern",
    "backend developer fresher",
    "data science intern",
    "machine learning intern",
]
JOB_SEARCH_HOURS_OLD = 72  # only listings posted in the last N hours

# Companies on public applicant-tracking-system feeds. Add more any time:
# the slug is the part of the company's careers URL, e.g.
#   boards.greenhouse.io/<slug>, jobs.lever.co/<slug>, jobs.ashbyhq.com/<slug>
# Unknown slugs are skipped and reported on the "Source Health" tab.
GREENHOUSE = [
    "razorpaysoftwareprivatelimited", "phonepe", "groww", "meesho", "postman",
    "browserstack", "druva", "rubrik", "databricks", "stripe", "airbnb",
    "coinbase", "cloudflare", "gitlab", "mongodb", "elastic", "twilio",
    "okta", "pinterest", "dropbox", "robinhood", "discord", "figma",
    "samsara", "datadog", "confluent", "hashicorp", "nutanix", "purestorage",
    "zscaler", "instacart", "lyft", "reddit", "affirm", "chime", "brex",
    "gojek", "grab", "agoda", "atlassian", "sprinklr", "innovaccer",
    "hackerrank", "chargebee", "freshworks", "sharechat", "dream11",
    "zeta", "slice", "jupiter", "cars24", "upgrad", "unacademy", "khatabook",
    "inmobi", "mindtickle", "whatfix", "icertis", "highradius", "lenskart",
]
LEVER = [
    "cred", "swiggy", "zomato", "paytm", "zeptonow", "dunzo", "spotify",
    "palantir", "plaid", "netflix", "rippling", "nium", "smallcase",
    "fampay", "jar-app", "kuku", "acko", "ola", "rapido", "urbancompany",
    "dukaan", "glean", "atlan", "hasura", "setu", "mpl", "pocketfm",
    "skit", "fi", "open", "toplyne", "zepto", "blinkit",
]
ASHBY = [
    "sarvam", "openai", "anthropic", "notion", "ramp", "linear", "vercel",
    "supabase", "replit", "perplexity", "cohere", "mistral", "deel",
    "posthog", "retool", "cursor", "elevenlabs", "zepto", "composio",
    "krutrim", "plivo", "bolna", "simplismart", "scaler", "physicswallah",
]

# Hackathons/contests closing within this many days go on "Closing Soon".
CLOSING_SOON_DAYS = 7
