"""
Gujarat Govt Jobs Auto-Scraper
Runs daily via GitHub Actions — scrapes OJAS, GPSC, GSSSB, NFSU, ISRO, SMC
Generates jobs.json → website reads it automatically
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime, date
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

TODAY = date.today().isoformat()
NOW   = datetime.now().strftime("%d %b %Y, %I:%M %p")

# ── Keywords to match Yogesh's profile ──────────────────────────────────────
MATCH_KEYWORDS = [
    "mechanical", "engineer", "robotics", "automation", "cnc", "technical",
    "instructor", "craftsman", "production", "manufacturing", "scientist",
    "workshop", "machinist", "fitter", "welder", "supervisor", "junior engineer",
    "assistant engineer", "junior technical", "industrial", "fabrication",
    "solidworks", "autocad", "diploma", "b.e", "b.tech", "graduate"
]

EXCLUDE_KEYWORDS = ["civil only", "electrical only", "chemical only"]

SALARY_KEYWORDS = ["44900", "40800", "56100", "35400", "38600", "level 6",
                   "level 7", "level 8", "level 9", "level 10", "pay band"]

# ── Portals to scrape ────────────────────────────────────────────────────────
PORTALS = [
    {
        "name": "OJAS Gujarat",
        "url": "https://ojas.gujarat.gov.in/AdvtList.aspx",
        "short": "ojas",
        "color": "teal"
    },
    {
        "name": "GPSC",
        "url": "https://gpsc.gujarat.gov.in/Advertisement",
        "short": "gpsc",
        "color": "purple"
    },
    {
        "name": "GSSSB",
        "url": "https://gsssb.gujarat.gov.in/advertisementlist",
        "short": "gsssb",
        "color": "amber"
    },
    {
        "name": "NFSU Career",
        "url": "https://nfsu.ac.in/career",
        "short": "nfsu",
        "color": "blue"
    },
    {
        "name": "ISRO SAC",
        "url": "https://www.isro.gov.in/Careers.html",
        "short": "isro",
        "color": "red"
    },
    {
        "name": "SMC Surat",
        "url": "https://www.suratmunicipal.gov.in/information/recruitment",
        "short": "smc",
        "color": "green"
    }
]


def safe_get(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ⚠ Could not fetch {url}: {e}")
        return None


def is_relevant(text):
    text_lower = text.lower()
    has_match = any(kw in text_lower for kw in MATCH_KEYWORDS)
    has_exclude = any(kw in text_lower for kw in EXCLUDE_KEYWORDS)
    return has_match and not has_exclude


def extract_date(text):
    """Try to find a date in text like 15/04/2026, 15-04-2026, 15 Apr 2026"""
    patterns = [
        r'\d{2}[/-]\d{2}[/-]\d{4}',
        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return "—"


def scrape_ojas():
    jobs = []
    html = safe_get("https://ojas.gujarat.gov.in/AdvtList.aspx")
    if not html:
        return jobs
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tr")
    for row in rows[1:40]:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue
        text = row.get_text(" ", strip=True)
        if not is_relevant(text):
            continue
        link_tag = row.find("a", href=True)
        link = "https://ojas.gujarat.gov.in/" + link_tag["href"].lstrip("./") if link_tag else "https://ojas.gujarat.gov.in"
        last_date = extract_date(cols[-1].get_text())
        jobs.append({
            "title": cols[1].get_text(strip=True) if len(cols) > 1 else text[:80],
            "org": "OJAS Gujarat",
            "portal": "ojas",
            "link": link,
            "lastDate": last_date,
            "notified": TODAY,
            "status": "open",
            "isNew": True
        })
    return jobs[:10]


def scrape_gpsc():
    jobs = []
    html = safe_get("https://gpsc.gujarat.gov.in/Advertisement")
    if not html:
        return jobs
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tr, .advt-row, .advertisement-list li, .list-group-item")
    for row in rows[:30]:
        text = row.get_text(" ", strip=True)
        if len(text) < 10:
            continue
        if not is_relevant(text):
            continue
        link_tag = row.find("a", href=True)
        href = link_tag["href"] if link_tag else ""
        if href and not href.startswith("http"):
            href = "https://gpsc.gujarat.gov.in" + href
        link = href or "https://gpsc.gujarat.gov.in/Advertisement"
        jobs.append({
            "title": text[:100],
            "org": "GPSC",
            "portal": "gpsc",
            "link": link,
            "lastDate": extract_date(text),
            "notified": TODAY,
            "status": "open",
            "isNew": True
        })
    return jobs[:8]


def scrape_gsssb():
    jobs = []
    html = safe_get("https://gsssb.gujarat.gov.in/advertisementlist")
    if not html:
        return jobs
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tr")
    for row in rows[1:30]:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        text = row.get_text(" ", strip=True)
        if not is_relevant(text):
            continue
        link_tag = row.find("a", href=True)
        href = link_tag["href"] if link_tag else ""
        if href and not href.startswith("http"):
            href = "https://gsssb.gujarat.gov.in" + href
        link = href or "https://gsssb.gujarat.gov.in"
        jobs.append({
            "title": cols[1].get_text(strip=True) if len(cols) > 1 else text[:80],
            "org": "GSSSB",
            "portal": "gsssb",
            "link": link,
            "lastDate": extract_date(text),
            "notified": TODAY,
            "status": "open",
            "isNew": True
        })
    return jobs[:8]


def scrape_nfsu():
    jobs = []
    html = safe_get("https://nfsu.ac.in/career")
    if not html:
        return jobs
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("a, li, .career-item, .job-listing, p")
    seen = set()
    for item in items:
        text = item.get_text(" ", strip=True)
        if len(text) < 15 or text in seen:
            continue
        seen.add(text)
        if not is_relevant(text):
            continue
        link_tag = item if item.name == "a" else item.find("a", href=True)
        href = link_tag["href"] if link_tag and link_tag.get("href") else "https://nfsu.ac.in/career"
        if href and not href.startswith("http"):
            href = "https://nfsu.ac.in/" + href.lstrip("/")
        jobs.append({
            "title": text[:100],
            "org": "NFSU Gandhinagar",
            "portal": "nfsu",
            "link": href,
            "lastDate": extract_date(text),
            "notified": TODAY,
            "status": "open",
            "isNew": True
        })
    return jobs[:5]


def scrape_isro():
    jobs = []
    html = safe_get("https://www.isro.gov.in/Careers.html")
    if not html:
        return jobs
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("table tr, .career-row, li, .job-row")
    for item in items[:30]:
        text = item.get_text(" ", strip=True)
        if len(text) < 10:
            continue
        if not is_relevant(text):
            continue
        link_tag = item.find("a", href=True) if item.name != "a" else item
        href = link_tag["href"] if link_tag and link_tag.get("href") else "https://www.isro.gov.in/Careers.html"
        if href and not href.startswith("http"):
            href = "https://www.isro.gov.in/" + href.lstrip("/")
        jobs.append({
            "title": text[:100],
            "org": "ISRO",
            "portal": "isro",
            "link": href,
            "lastDate": extract_date(text),
            "notified": TODAY,
            "status": "open",
            "isNew": True
        })
    return jobs[:5]


def scrape_smc():
    jobs = []
    html = safe_get("https://www.suratmunicipal.gov.in/information/recruitment")
    if not html:
        return jobs
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("table tr, .recruitment-item, li, a")
    seen = set()
    for item in items[:30]:
        text = item.get_text(" ", strip=True)
        if len(text) < 10 or text in seen:
            continue
        seen.add(text)
        if not is_relevant(text):
            continue
        link_tag = item if item.name == "a" else item.find("a", href=True)
        href = ""
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            if not href.startswith("http"):
                href = "https://www.suratmunicipal.gov.in" + href
        link = href or "https://www.suratmunicipal.gov.in/information/recruitment"
        jobs.append({
            "title": text[:100],
            "org": "SMC Surat Municipal Corporation",
            "portal": "smc",
            "link": link,
            "lastDate": extract_date(text),
            "notified": TODAY,
            "status": "open",
            "isNew": True
        })
    return jobs[:5]


# ── BASE JOBS (always included — manually verified) ──────────────────────────
BASE_JOBS = [
    {
        "id": "gpsc-ae-279",
        "title": "Assistant Engineer — Mechanical (Class 2 Gazetted)",
        "org": "GPSC — GWSSB / GMB / New Municipal Corps",
        "portal": "gpsc",
        "field": "eng",
        "fieldLabel": "Engineering",
        "govtType": "State",
        "notified": "31 Jan 2026",
        "applyFrom": "31 Jan 2026",
        "lastDate": "16 Feb 2026 (Closed)",
        "salary": "₹44,900 – ₹1,42,400",
        "salaryNum": 44900,
        "vacancies": "279",
        "stVac": "~42 ST",
        "stFee": "FREE",
        "statusClass": "sp-upcoming",
        "statusLabel": "EXAM APR 26",
        "isOpen": False,
        "isUrgent": False,
        "isST": True,
        "fit": 92,
        "fitLabel": "Best Match",
        "link": "https://gpsc-ojas.gujarat.gov.in",
        "isNew": False,
        "examStages": [
            {"stage":"Prelim","name":"Preliminary Exam","mode":"OMR MCQ","marks":"200","duration":"2 hrs","neg":"0.33"},
            {"stage":"Mains","name":"Mains Written Exam","mode":"Offline Descriptive","marks":"300","duration":"3 hrs","neg":"None"},
            {"stage":"Final","name":"Viva-Voce","mode":"Offline","marks":"50","duration":"—","neg":"—"}
        ],
        "syllabus":["SOM","TOM","Fluid Mechanics","Thermodynamics","Manufacturing Engg","Machine Design","CAD/CAM","Engineering Maths","Gujarat GK"],
        "docsNeeded":["ST Caste Certificate","GTU Degree","All Marksheets","Domicile","Aadhaar","Internship Certs","Photo"],
        "note": "279 vacancies. ~42 reserved for ST. Prelim exam April 26, 2026. Prepare now — 5 weeks left."
    },
    {
        "id": "smc-ae-mech",
        "title": "Assistant Engineer — Mechanical",
        "org": "SMC — Surat Municipal Corporation",
        "portal": "smc",
        "field": "mun",
        "fieldLabel": "Municipal",
        "govtType": "State (Municipal)",
        "notified": "11 Mar 2026",
        "applyFrom": "01 Apr 2026",
        "lastDate": "15 Apr 2026",
        "salary": "₹44,900 – ₹1,42,400",
        "salaryNum": 44900,
        "vacancies": "~25",
        "stVac": "~4 ST",
        "stFee": "₹250",
        "statusClass": "sp-open",
        "statusLabel": "OPENS APR 1",
        "isOpen": True,
        "isUrgent": False,
        "isST": True,
        "fit": 97,
        "fitLabel": "Best Match — Home City",
        "link": "https://suratmunicipal.gov.in/information/recruitment",
        "isNew": False,
        "examStages": [
            {"stage":"Stage 1","name":"Written Exam (Objective)","mode":"OMR/CBT","marks":"150","duration":"2 hrs","neg":"0.25"},
            {"stage":"Stage 2","name":"Document Verification","mode":"Offline","marks":"—","duration":"—","neg":"—"}
        ],
        "syllabus":["SOM","TOM","Fluid Mechanics","Manufacturing Processes","Engineering Drawing","Thermodynamics","Material Science","Gujarat GK"],
        "docsNeeded":["ST Certificate","GTU Degree","Marksheets","Domicile","Internship Certs","Aadhaar","Photo"],
        "note": "Surat-based. Apply from April 1. 2295 total vacancies in this notification. AE Mech is ideal for Yogesh."
    },
    {
        "id": "nfsu-technical",
        "title": "Scientific / Technical Officer",
        "org": "NFSU Gandhinagar (MHA — Central Govt)",
        "portal": "nfsu",
        "field": "tech",
        "fieldLabel": "Technical",
        "govtType": "Central",
        "notified": "23 Feb 2026",
        "applyFrom": "23 Feb 2026",
        "lastDate": "23 Mar 2026 (Closed)",
        "salary": "₹44,900 – ₹1,42,400",
        "salaryNum": 44900,
        "vacancies": "82",
        "stVac": "~6 ST",
        "stFee": "FREE",
        "statusClass": "sp-closed",
        "statusLabel": "CLOSED",
        "isOpen": False,
        "isUrgent": False,
        "isST": True,
        "fit": 95,
        "fitLabel": "Best Match",
        "link": "https://nfsu.ac.in/career",
        "isNew": False,
        "examStages": [
            {"stage":"Stage 1","name":"Written Test (CBT)","mode":"Online MCQ","marks":"100","duration":"90 min","neg":"1/4"},
            {"stage":"Stage 2","name":"Interview / Skill Test","mode":"Offline","marks":"—","duration":"—","neg":"—"}
        ],
        "syllabus":["Mechanical Engineering Core","Robotics & Automation","CNC Programming","Material Science","Aptitude","English & GK"],
        "docsNeeded":["ST Certificate","GTU Degree","Marksheets","Internship Certs","Photo","Aadhaar"],
        "note": "Application closed. Watch for next notification cycle."
    },
    {
        "id": "isro-sac",
        "title": "Scientist / Engineer SC — Robotics / Mechatronics",
        "org": "ISRO SAC, Ahmedabad (Central Govt)",
        "portal": "isro",
        "field": "tech",
        "fieldLabel": "Technical",
        "govtType": "Central",
        "notified": "Dec 2025 (prev cycle)",
        "applyFrom": "Dec 2025",
        "lastDate": "Feb 2026 (Closed)",
        "salary": "₹56,100 – ₹2,08,700",
        "salaryNum": 56100,
        "vacancies": "~49",
        "stVac": "7.5%",
        "stFee": "FREE",
        "statusClass": "sp-watch",
        "statusLabel": "NEXT: MID-2026",
        "isOpen": False,
        "isUrgent": False,
        "isST": True,
        "fit": 85,
        "fitLabel": "Strong Match",
        "link": "https://sac.gov.in",
        "isNew": False,
        "examStages": [
            {"stage":"Stage 1","name":"Written Test (ICRB)","mode":"CBT MCQ","marks":"100","duration":"90 min","neg":"0.33"},
            {"stage":"Stage 2","name":"Technical Interview","mode":"Offline","marks":"—","duration":"—","neg":"—"}
        ],
        "syllabus":["Advanced Robotics","Control Systems","FANUC Robots","Mechatronics","Fluid Mechanics","Thermodynamics","Engineering Maths","Aptitude"],
        "docsNeeded":["ST Certificate","GTU Degree (65%+)","FANUC certs","Internship Certs","iACE PGP certificate","Photo","Aadhaar"],
        "note": "Highest paying tech job in Ahmedabad. Watch sac.gov.in for next cycle mid-2026."
    },
    {
        "id": "gsssb-instructor",
        "title": "Supervisor Instructor — CNC / Production / Mechanical",
        "org": "GSSSB — Govt ITI Gujarat",
        "portal": "gsssb",
        "field": "inst",
        "fieldLabel": "Instructor",
        "govtType": "State (GSSSB)",
        "notified": "02 Mar 2026",
        "applyFrom": "02 Mar 2026",
        "lastDate": "16 Mar 2026 (Closed)",
        "salary": "₹40,800 (Fixed 5 yrs)",
        "salaryNum": 40800,
        "vacancies": "203 total",
        "stVac": "15%",
        "stFee": "₹200",
        "statusClass": "sp-upcoming",
        "statusLabel": "CBT UPCOMING",
        "isOpen": False,
        "isUrgent": False,
        "isST": True,
        "fit": 88,
        "fitLabel": "Best Match — World Skills Rank",
        "link": "https://ojas.gujarat.gov.in",
        "isNew": False,
        "examStages": [
            {"stage":"Stage 1","name":"CBT Written Test","mode":"Online MCQ","marks":"100","duration":"90 min","neg":"0.25"},
            {"stage":"Stage 2","name":"Practical / Skill Demo","mode":"Offline","marks":"Pass/Fail","duration":"—","neg":"—"}
        ],
        "syllabus":["CNC Programming (G/M code)","FANUC Controller","Mech trade theory","Manufacturing processes","Workshop Safety","Teaching methodology","Lean / 5S"],
        "docsNeeded":["ST Certificate","GTU Degree","World Skills Certificate","FANUC certs","Internship Certs","Aadhaar","Photo"],
        "note": "Your World Skills District Rank 1 is a direct credential here. ST posting priority near Surat tribal belt."
    },
    {
        "id": "craft-instructor-iti",
        "title": "Craft Instructor — CNC / Robotics / Mechanical Trade",
        "org": "Govt ITI — Directorate of Employment & Training, Gujarat",
        "portal": "ojas",
        "field": "inst",
        "fieldLabel": "Instructor",
        "govtType": "State",
        "notified": "Periodic",
        "applyFrom": "Watch OJAS",
        "lastDate": "Watch OJAS",
        "salary": "₹40,000 – ₹60,000",
        "salaryNum": 40000,
        "vacancies": "Periodic batches",
        "stVac": "15% + tribal priority",
        "stFee": "FREE",
        "statusClass": "sp-watch",
        "statusLabel": "WATCH OJAS",
        "isOpen": False,
        "isUrgent": False,
        "isST": True,
        "fit": 90,
        "fitLabel": "Best Match",
        "link": "https://ojas.gujarat.gov.in",
        "isNew": False,
        "examStages": [
            {"stage":"Stage 1","name":"Written Test","mode":"MCQ","marks":"100","duration":"90 min","neg":"0.25"},
            {"stage":"Stage 2","name":"Trade Practical Test","mode":"Offline","marks":"Pass/Fail","duration":"—","neg":"—"}
        ],
        "syllabus":["CNC Trade Theory","FANUC Programming","Workshop Calculations","Engineering Drawing","Trade Pedagogy","Safety & HSE"],
        "docsNeeded":["ST Certificate","GTU Degree","World Skills Cert","Internship Certs","Aadhaar","Photo"],
        "note": "Priority posting near Umarpada / tribal belt for ST. Permanent Govt job with pension."
    }
]


def load_existing_jobs():
    path = "data/jobs.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"jobs": BASE_JOBS, "scraped": [], "lastUpdated": NOW, "newCount": 0}


def run():
    print(f"\n🔍 Gujarat Govt Jobs Scraper — {NOW}")
    print("=" * 50)

    existing = load_existing_jobs()
    existing_ids = {j.get("id", j.get("title", "")) for j in existing.get("scraped", [])}

    all_scraped = []
    new_count = 0

    scrapers = [
        ("OJAS Gujarat", scrape_ojas),
        ("GPSC",         scrape_gpsc),
        ("GSSSB",        scrape_gsssb),
        ("NFSU",         scrape_nfsu),
        ("ISRO",         scrape_isro),
        ("SMC Surat",    scrape_smc),
    ]

    for name, fn in scrapers:
        print(f"\n  Scraping {name}...")
        try:
            jobs = fn()
            for j in jobs:
                uid = j.get("title", "")[:50]
                j["isNew"] = uid not in existing_ids
                if j["isNew"]:
                    new_count += 1
                    print(f"    ✅ NEW: {j['title'][:60]}")
                else:
                    print(f"    ✓  {j['title'][:60]}")
            all_scraped.extend(jobs)
            time.sleep(1)
        except Exception as e:
            print(f"    ⚠ Error: {e}")

    os.makedirs("data", exist_ok=True)

    output = {
        "lastUpdated": NOW,
        "lastUpdatedISO": datetime.now().isoformat(),
        "newCount": new_count,
        "totalScraped": len(all_scraped),
        "jobs": BASE_JOBS,
        "scraped": all_scraped,
        "portals": [p["name"] for p in PORTALS],
        "profile": {
            "name": "Yogeshkumar Vasava",
            "category": "ST",
            "education": "B.E. Mechanical (GTU) · iACE PGP",
            "skills": ["FANUC Robotics", "CNC Milling", "SolidWorks", "Lean Mfg", "3D Printing"],
            "minSalary": 30000
        }
    }

    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! {len(all_scraped)} scraped | {new_count} new | Saved to data/jobs.json")
    return new_count


if __name__ == "__main__":
    new = run()
    # Exit code 1 signals new jobs found (triggers notification step in Actions)
    exit(0 if new == 0 else 1)
