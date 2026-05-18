import re
import logging
from typing import List, Set, Tuple
from sqlalchemy.orm import Session
from rank_bm25 import BM25Okapi
from .. import models, schemas
from .vector_store import cosine_similarity, deserialize_embedding

logger = logging.getLogger("matcher")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

# Core tech keywords that receive a heavy multiplier
CORE_SKILLS = {
    "python", "react", "fastapi", "javascript", "typescript", "sql", "postgresql", "mysql",
    "mongodb", "redis", "docker", "kubernetes", "aws", "gcp", "django", "flask", "node", "nodejs",
    "git", "rest api", "graphql", "machine learning", "pytorch", "tensorflow", "apis",
    "backend engineering", "frontend engineering", "software development", "full stack development", "system design"
}

# Generic/fluff words that should have minimal or no impact
GENERIC_WORDS = {
    "technical", "training", "support", "management", "team", "hardworking", "motivated", "detail-oriented"
}

TECH_SKILLS = CORE_SKILLS.union({
    "vue", "angular", "express", "spring", "java", "kotlin", "swift", "flutter", "react native",
    "azure", "ci/cd", "html", "css", "sass", "rust", "golang", "c++", "c#", "ruby", "rails",
    "php", "laravel", "deep learning", "nlp", "pandas", "numpy", "scikit-learn", "data science",
    "devops", "qa", "testing", "figma", "ui/ux", "webflow"
})

def get_skill_weight(skill: str) -> float:
    if skill in CORE_SKILLS:
        return 4.0
    if skill in GENERIC_WORDS:
        return 0.1
    return 1.0

def extract_skills(text: str) -> Set[str]:
    if not text:
        return set()
    text_lower = text.lower()
    found = set()
    
    multi_word_skills = [
        "backend engineering", "frontend engineering", "software development", 
        "full stack development", "rest api", "react native", "machine learning", 
        "deep learning", "data science", "ui/ux", "system design"
    ]
    for skill in multi_word_skills:
        if skill in text_lower:
            found.add(skill)
            text_lower = text_lower.replace(skill, "")

    cleaned = re.sub(r"[^a-z0-9#+]", " ", text_lower)
    tokens = cleaned.split()
    for token in tokens:
        if token in TECH_SKILLS:
            found.add(token)
            
    return found

def is_tech_candidate(desired_roles: str, skills: str) -> bool:
    text = f"{desired_roles} {skills}".lower()
    tech_keywords = [
        "software", "developer", "engineer", "programmer", "coder", "architect", 
        "data scientist", "data engineer", "machine learning", "devops", 
        "fullstack", "full stack", "frontend", "front-end", "backend", "back-end",
        "web developer", "sde", "tech lead", "technical lead", "system engineer", "it "
    ]
    return any(keyword in text for keyword in tech_keywords)

def is_non_tech_job(title: str, description: str) -> bool:
    title_lower = title.lower()
    non_tech_patterns = [
        r"\btherapist\b", r"\btherapy\b", r"\bcounselor\b", r"\bcounseling\b", r"\bpsychologist\b", 
        r"\bnurse\b", r"\bnursing\b", r"\bphysician\b", r"\bdoctor\b", r"\bclinical\b", r"\bhealthcare\b",
        r"\baccountant\b", r"\baccounting\b", r"\bbookkeeper\b", r"\btax\b", r"\bauditor\b", r"\bfinance manager\b",
        r"\blawyer\b", r"\battorney\b", r"\bparalegal\b", r"\blegal\b",
        r"\bsales\b", r"\bretail\b", r"\bstore manager\b", r"\btelemarketing\b", r"\bmarketing\b", r"\bseo\b",
        r"\bhuman resources\b", r"\brecruiter\b", r"\btalent acquisition\b", r"\bhr\b",
        r"\bcustomer service\b", r"\bhelpdesk\b", r"\bsupport agent\b", r"\bcustomer support\b", r"\boperations\b"
    ]
    
    tech_keywords = [
        "software", "developer", "engineer", "programmer", "coder", "architect", 
        "data scientist", "data engineer", "machine learning", "devops", 
        "fullstack", "frontend", "backend", "sde"
    ]
    
    is_non_tech_domain = any(re.search(pattern, title_lower) for pattern in non_tech_patterns)
    is_tech_role = any(keyword in title_lower for keyword in tech_keywords)
    return is_non_tech_domain and not is_tech_role

class JobMatcher:
    def __init__(self, min_score: float = 0.8, fallback_count: int = 5):
        self.min_score = min_score
        self.fallback_count = fallback_count

    def find_matches(self, db: Session, student_embedding: List[float], profile_text: str, page: int = 1, limit: int = 20) -> tuple[List[schemas.JobPosting], bool, str]:
        logger.info(f"Matcher initiated. Parameters - min_score: {self.min_score}, page: {page}, limit: {limit}")
        scored_jobs: List[schemas.JobPosting] = []
        
        jobs = db.query(models.JobPosting).filter(models.JobPosting.is_active == True).all()
        logger.info(f"Retrieved {len(jobs)} active jobs from SQLite database for scanning.")
        
        student_skills = extract_skills(profile_text)
        candidate_is_tech = is_tech_candidate(profile_text, profile_text)
        logger.info(f"Student extracted core skills: {student_skills}. Is tech candidate classification: {candidate_is_tech}")
        
        tokenized_corpus = []
        job_list = []
        job_embeddings = []
        job_ids = []
        
        for job in jobs:
            job_desc = job.description or ''
            if candidate_is_tech:
                if is_non_tech_job(job.title or '', job_desc):
                    # Skip non-tech job profiles aggressively for tech candidates
                    continue

            job_text = ' '.join([job.title or '', job.company or '', job.location or '', job_desc]).lower()
            tokenized_corpus.append(job_text.split())
            job_list.append(job)
            
            embedding = deserialize_embedding(job.embedding)
            if embedding:
                job_embeddings.append(embedding)
                job_ids.append(job.id)
            else:
                # Add default embedding if missing
                job_embeddings.append([0.0]*384)
                job_ids.append(job.id)
                
        logger.info(f"After domain filtering, {len(job_list)} jobs are eligible for scoring.")
        
        if not job_list:
            logger.warning("No eligible jobs left in dataset to recommend.")
            return [], True, "No suitable jobs found."

        # Compute BM25 scores safely
        bm25_scores = [0.0] * len(job_list)
        try:
            bm25 = BM25Okapi(tokenized_corpus)
            query_tokens = profile_text.lower().split()
            bm25_scores = bm25.get_scores(query_tokens)
            max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
            normalized_bm25 = [score / max_bm25 for score in bm25_scores]
            logger.info("BM25 lexical scoring computed successfully.")
        except Exception as bm_err:
            logger.error(f"BM25 lexical calculations failed: {bm_err}. Defaulting to zero.")
            normalized_bm25 = [0.0] * len(job_list)

        # Compute pure-python cosine similarity instead of FAISS to keep local dependencies super stable
        semantic_results = {}
        logger.info("Calculating pure-Python cosine similarity scores for dense embeddings...")
        for job_id, emb in zip(job_ids, job_embeddings):
            try:
                sim = cosine_similarity(student_embedding, emb)
                semantic_results[job_id] = float(sim)
            except Exception as sim_err:
                logger.error(f"Failed calculating cosine similarity for job {job_id}: {sim_err}")
                semantic_results[job_id] = 0.0

        for i, job in enumerate(job_list):
            job_text = ' '.join([job.title or '', job.company or '', job.location or '', job.description or ''])
            job_skills = extract_skills(job_text)
            
            semantic_score = semantic_results.get(job.id, 0.0)
            bm25_score = normalized_bm25[i]
            
            if job_skills:
                matched_skills = student_skills.intersection(job_skills)
                missing_skills = job_skills.difference(student_skills)
                
                weighted_matched = sum(get_skill_weight(s) for s in matched_skills)
                weighted_total = sum(get_skill_weight(s) for s in job_skills)
                skill_overlap_ratio = round(weighted_matched / weighted_total, 3) if weighted_total > 0 else 0.0
            else:
                matched_skills = set()
                missing_skills = set()
                skill_overlap_ratio = 0.0

            # Dynamic score: 45% skills, 35% semantic, 20% lexical
            if job_skills:
                combined_score = round((0.45 * skill_overlap_ratio) + (0.35 * semantic_score) + (0.20 * bm25_score), 3)
            else:
                combined_score = round((0.60 * semantic_score) + (0.40 * bm25_score), 3)
                
            # Bound core score
            if combined_score > 0.90:
                if not (skill_overlap_ratio >= 0.95 and semantic_score >= 0.90):
                    combined_score = 0.90
                
            scored_jobs.append(schemas.JobPosting(
                id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                url=job.url,
                score=combined_score,
                source=job.source or "unknown",
                match_breakdown=schemas.MatchBreakdown(
                    semantic_similarity=float(semantic_score),
                    skill_overlap_ratio=float(skill_overlap_ratio),
                    matched_skills=list(matched_skills),
                    missing_skills=list(missing_skills)
                )
            ))

        scored_jobs.sort(key=lambda item: item.score or 0.0, reverse=True)
        
        # Pagination index limits
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        strict_matches = [job for job in scored_jobs if (job.score or 0.0) >= self.min_score]
        
        if strict_matches:
            logger.info(f"Found {len(strict_matches)} strict matches with score >= {self.min_score}")
            return strict_matches[start_idx:end_idx], False, f"Successfully recommended top highly-aligned jobs!"
            
        fallback_matches = scored_jobs[start_idx:end_idx]
        logger.info(f"No strict matches. Returning {len(fallback_matches)} top fallback matches instead.")
        message = (
            "We couldn't find job listings with strict 80%+ alignment based on your profile. "
            "Showing the top fallback matches:"
        )
        return fallback_matches, True, message


