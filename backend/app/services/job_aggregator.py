import httpx
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import re
from .embeddings import generate_embedding
from .. import models
from ..crud import get_job_by_url, create_job

logger = logging.getLogger("job_aggregator")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

def clean_html(html_text: str) -> str:
    if not html_text:
        return ""
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text)
        return text
    except Exception:
        return html_text

def normalize_company_name(name: str) -> str:
    if not name:
        return "Unknown Company"
    name = name.lower()
    suffixes = [' pvt ltd', ' private limited', ' ltd', ' limited', ' inc', ' llc', ' corp']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name.strip().title()

async def fetch_internshala(client: httpx.AsyncClient, query: str = "") -> List[Dict]:
    logger.info("Fetching from Internshala (Simulated data to bypass Cloudflare)...")
    mapped = [
        {
            "title": "Software Engineering Intern",
            "company": "TechVeda India",
            "location": "Bangalore",
            "description": "Looking for students skilled in Python, Django, and React for a 6-month internship. You will collaborate on core features, build responsive UIs, and work with SQLite/PostgreSQL databases.",
            "url": "https://internshala.com/internships/software-development-internship/",
            "source": "internshala"
        },
        {
            "title": "React Frontend Developer Intern",
            "company": "Kyrotics Systems",
            "location": "Remote (India)",
            "description": "Excellent opportunity for React frontend engineers. Experience with TailwindCSS, Framer Motion, and API integrations is highly valued.",
            "url": "https://internshala.com/internships/reactjs-internship/",
            "source": "internshala"
        }
    ]
    logger.info(f"Loaded {len(mapped)} simulated jobs for Internshala.")
    return mapped

async def fetch_instahyre(client: httpx.AsyncClient, query: str = "") -> List[Dict]:
    logger.info("Fetching from Instahyre (Simulated data to bypass bot protection)...")
    mapped = [
        {
            "title": "Backend Developer - Fresher",
            "company": "Razorpay",
            "location": "Bangalore",
            "description": "Building scalable payment APIs using Python, FastAPI, and PostgreSQL. Great for freshers who know backend engineering principles, data structures, and database optimization.",
            "url": "https://instahyre.com/job-mock-razorpay-backend",
            "source": "instahyre"
        },
        {
            "title": "Python Developer",
            "company": "Infosys",
            "location": "Remote",
            "description": "Looking for junior python developers with sound knowledge of FastAPI, standard SQL queries, Git, and automated testing.",
            "url": "https://instahyre.com/job-mock-infosys-python",
            "source": "instahyre"
        }
    ]
    logger.info(f"Loaded {len(mapped)} simulated jobs for Instahyre.")
    return mapped

async def fetch_linkedin_mock(client: httpx.AsyncClient, query: str = "") -> List[Dict]:
    logger.info("Fetching from LinkedIn (Simulated premium data for stabilization)...")
    query_lower = query.lower() if query else "software engineer"
    
    all_mock_jobs = [
        {
            "title": "Software Engineer Intern - Backend",
            "company": "Google India",
            "location": "Bangalore, Karnataka",
            "description": "Join Google's cloud database engineering team. We are looking for interns with solid understanding of Python, FastAPI, Go, algorithms, and system design. You will write high-performance APIs and query optimizers.",
            "url": "https://www.google.com/about/careers/applications/jobs/results/?q=Software%20Engineer%20Intern%20Backend",
            "source": "linkedin"
        },
        {
            "title": "Full Stack Developer",
            "company": "Microsoft",
            "location": "Hyderabad, Telangana",
            "description": "Microsoft is seeking a Full Stack Developer experienced with React, TypeScript, C#, and Azure. Experience building responsive web applications, working with CSS/Tailwind, and state management is required.",
            "url": "https://careers.microsoft.com/us/en/search-results?q=Full%20Stack%20Developer",
            "source": "linkedin"
        },
        {
            "title": "Data Engineer",
            "company": "Amazon",
            "location": "Chennai, Tamil Nadu",
            "description": "We are seeking Data Engineers to design scale storage pipelines. Proficiency in python, AWS, SQL databases, Spark, and ETL workflows is highly desired. Experience with big data technologies is a plus.",
            "url": "https://www.amazon.jobs/en/search?base_query=Data%20Engineer&loc_query=India",
            "source": "linkedin"
        },
        {
            "title": "Frontend Engineer (React)",
            "company": "Flipkart",
            "location": "Bangalore, India",
            "description": "Looking for React Frontend Specialists. Build premium ecommerce user interfaces with optimized render times. Solid knowledge of HTML5, CSS3, vanilla JS, React, and modular styling is mandatory.",
            "url": "https://www.linkedin.com/jobs/search/?keywords=Frontend%20Engineer%20React%20Flipkart&location=Bangalore",
            "source": "linkedin"
        },
        {
            "title": "Backend Engineering Fellow",
            "company": "CRED",
            "location": "Remote (India)",
            "description": "Seeking exceptional backend fellows. Stack is Python, FastAPI, PostgreSQL, Redis, and Docker. Build low-latency financial ledger endpoints and transaction security pipelines.",
            "url": "https://www.linkedin.com/jobs/search/?keywords=Backend%20Engineer%20CRED%20Python%20FastAPI",
            "source": "linkedin"
        }
    ]
    
    # Filter or prioritize based on the search query terms to make matches highly relevant!
    terms = query_lower.split()
    matched = []
    for job in all_mock_jobs:
        match_count = 0
        job_content = (job["title"] + " " + job["description"] + " " + job["company"]).lower()
        for term in terms:
            if term in job_content:
                match_count += 1
        if match_count > 0:
            matched.append(job)
            
    # If no jobs match specific terms, return a subset of all mock jobs as a fallback
    result = matched if matched else all_mock_jobs[:3]
    logger.info(f"Generated {len(result)} simulated jobs for LinkedIn matching search query '{query}'.")
    return result


async def fetch_remotive(client: httpx.AsyncClient, query: str = "") -> List[Dict]:
    logger.info("Attempting to fetch remote jobs from Remotive API...")
    url = "https://remotive.com/api/remote-jobs?limit=10"
    if query:
        url += f"&search={httpx.utils.quote(query)}"
    try:
        response = await client.get(url, timeout=5.0)
        logger.info(f"Remotive HTTP status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            mapped = []
            for j in jobs:
                # Include worldwide or India allowed remote jobs
                loc = j.get("candidate_required_location", "").lower()
                if "india" in loc or "worldwide" in loc or "anywhere" in loc:
                    mapped.append({
                        "title": j.get("title", "Job Posting"),
                        "company": normalize_company_name(j.get("company_name", "Unknown")),
                        "location": j.get("candidate_required_location", "Remote"),
                        "description": clean_html(j.get("description", "")),
                        "url": j.get("url"),
                        "source": "remotive"
                    })
            logger.info(f"Parsed {len(mapped)} jobs matching India/Worldwide criteria from Remotive.")
            return mapped
    except Exception as e:
        logger.error(f"Error fetching Remotive: {e}")
    return []

class JobAggregator:
    async def aggregate(self, db: Session, query: str = 'software engineer') -> List[models.JobPosting]:
        logger.info(f"Starting Job Aggregator Pipeline for query: '{query}'")
        raw_jobs = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Sequentially scrape websites with error catching to keep pipeline extremely stable
        # During stabilization, we restrict requests to 2 highly stable, deterministic sources: LinkedIn mock data + Internshala sample data
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            # 1. LinkedIn Mock Data
            try:
                linkedin_jobs = await fetch_linkedin_mock(client, query=query)
                raw_jobs.extend(linkedin_jobs)
            except Exception as e:
                logger.error(f"LinkedIn mock fetch failed sequentially: {e}")

            # 2. Internshala Simulated Data (Sample data)
            try:
                internshala_jobs = await fetch_internshala(client, query=query)
                raw_jobs.extend(internshala_jobs)
            except Exception as e:
                logger.error(f"Internshala fetch failed sequentially: {e}")


        # Final check: If absolutely no jobs are fetched, add fallback hardcoded jobs
        if not raw_jobs:
            logger.warning("All scraping failed or returned 0 results. Injecting baseline fallback jobs into corpus.")
            raw_jobs = [
                {
                    "title": "Junior Python Developer",
                    "company": "Acme Tech India",
                    "location": "Bangalore / Remote",
                    "description": "Looking for entry-level Software Engineers. Experience with Python, Django, FastAPI, React, SQL, and database concepts is highly desirable.",
                    "url": "https://acme.example.com/careers/junior-python-dev",
                    "source": "fallback"
                },
                {
                    "title": "Associate Web Developer (React)",
                    "company": "Cyber Solutions Ltd",
                    "location": "Remote",
                    "description": "Familiarity with modern JavaScript framework React, UIs, Tailwind CSS, REST APIs, Git, and web application components.",
                    "url": "https://cybersol.example.com/careers/assoc-react-dev",
                    "source": "fallback"
                }
            ]

        logger.info(f"Aggregator fetched a total of {len(raw_jobs)} jobs. Committing new entries to database...")

        stored_jobs = []
        for payload in raw_jobs:
            if not payload.get('url'):
                continue
            try:
                stored = self._store_job(db, payload)
                if stored:
                    stored_jobs.append(stored)
            except Exception as e:
                logger.error(f"Failed to store parsed job payload for '{payload.get('url')}': {e}", exc_info=True)

        logger.info(f"Database sync completed. Total active job listings available: {len(stored_jobs)}")
        return stored_jobs

    def _store_job(self, db: Session, payload: Dict) -> Optional[models.JobPosting]:
        existing = get_job_by_url(db, payload['url'])
        if existing:
            return existing
            
        existing_title_company = db.query(models.JobPosting).filter(
            models.JobPosting.title == payload['title'],
            models.JobPosting.company == payload['company'],
            models.JobPosting.source == payload.get('source')
        ).first()
        
        if existing_title_company:
            return existing_title_company

        # Embedding generation
        embedding_text = ' '.join([
            payload.get('title', ''),
            payload.get('company', ''),
            payload.get('location', ''),
            payload.get('description', '')
        ])
        
        try:
            embedding = generate_embedding(embedding_text)
        except Exception as e:
            logger.error(f"Embedding generation failed for job storing: {e}")
            embedding = [0.0] * 384
            
        return create_job(db, {
            'title': payload['title'],
            'company': payload['company'],
            'location': payload['location'],
            'description': payload['description'],
            'url': payload['url'],
            'source': payload.get('source', 'unknown'),
            'embedding': embedding,
        })


