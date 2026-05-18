import requests
from bs4 import BeautifulSoup
from typing import List, Dict


def parse_skills_from_text(text: str) -> List[str]:
    tokens = {word.strip('.,()[]').lower() for word in text.split()}
    return [token for token in tokens if len(token) > 2]


def sample_job_feed() -> List[Dict]:
    return [
        {
            'title': 'Software Engineering Intern',
            'company': 'CareerLaunch',
            'location': 'Remote',
            'description': 'Software engineering internship for students with Python, SQL, and cloud fundamentals.',
            'url': 'https://example.com/jobs/1'
        },
        {
            'title': 'Frontend Developer Intern',
            'company': 'CampusHire',
            'location': 'New York, NY',
            'description': 'Looking for React, JavaScript, HTML, CSS, and UX-focused students.',
            'url': 'https://example.com/jobs/2'
        },
    ]


def indeed_job_feed(query: str = 'software intern', location: str = 'remote') -> List[Dict]:
    url = f'https://www.indeed.com/jobs?q={requests.utils.quote(query)}&l={requests.utils.quote(location)}&limit=10'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    response = requests.get(url, headers=headers, timeout=10)
    jobs = []
    if response.status_code != 200:
        return jobs
    soup = BeautifulSoup(response.text, 'html.parser')
    cards = soup.select('a.tapItem')[:8]
    for card in cards:
        title = card.select_one('h2.jobTitle')
        company = card.select_one('span.companyName')
        location_el = card.select_one('div.companyLocation')
        url_path = card.get('href')
        jobs.append({
            'title': title.get_text(strip=True) if title else 'Job',
            'company': company.get_text(strip=True) if company else 'Unknown',
            'location': location_el.get_text(strip=True) if location_el else location,
            'description': ' '.join(p.get_text(strip=True) for p in card.select('div.job-snippet span')),
            'url': f'https://www.indeed.com{url_path}' if url_path else 'https://www.indeed.com'
        })
    return jobs


def gather_jobs(student_skills: str = '', desired_roles: str = '') -> List[Dict]:
    query = desired_roles or 'student intern'
    try:
        indeed = indeed_job_feed(query=query)
    except Exception:
        indeed = []
    sample = sample_job_feed()
    return sample + indeed
