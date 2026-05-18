import os
import tempfile
import time
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine
from .services.resume_parser import parse_resume
from .services.embeddings import generate_embedding
from .services.job_aggregator import JobAggregator
from .services.matcher import JobMatcher
from .services.caching import cache_response


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title='Job Matching Portal - Production AI')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def build_profile_text(fields: list[str]) -> str:
    return ' '.join(field.strip() for field in fields if field and field.strip())

import logging

# Configure logger
logger = logging.getLogger("main_api")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)

@app.post('/api/match', response_model=schemas.MatchResponse)
async def match_jobs(
    name: str = Form(...),
    email: str = Form(...),
    education: str = Form(''),
    skills: str = Form(''),
    experience: str = Form(''),
    desired_roles: str = Form(''),
    page: int = Form(1),
    limit: int = Form(20),
    resume: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    logger.info(f"--- Incoming request '/api/match' from {name} <{email}> ---")
    logger.info(f"Form values - Education: '{education}', Skills: '{skills}', Experience: '{experience}', Desired Roles: '{desired_roles}'")
    
    try:
        # Create student profile
        logger.info("Step 1/5: Creating student record in database...")
        student_data = schemas.StudentCreate(
            name=name,
            email=email,
            education=education,
            skills=skills,
            experience=experience,
            desired_roles=desired_roles,
        )
        student = crud.create_student(db, student_data)
        logger.info(f"Successfully created student database record. ID: {student.id}")
    except Exception as db_err:
        logger.error(f"Error creating student record: {db_err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error saving profile: {str(db_err)}")

    resume_text = ''
    resume_parsing_time = 0.0
    if resume is not None and resume.filename:
        logger.info(f"Step 2/5: Processing resume file: '{resume.filename}'")
        try:
            start_parse = time.perf_counter()
            suffix = os.path.splitext(resume.filename)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(await resume.read())
                temp_path = temp_file.name
            
            logger.info(f"Saved uploaded resume temporarily at '{temp_path}'. Parsing text...")
            resume_text = parse_resume(temp_path) or ''
            logger.info(f"Parsed {len(resume_text)} characters of text from resume.")
            
            try:
                os.unlink(temp_path)
            except OSError as unlink_err:
                logger.warning(f"Failed to delete temp resume file '{temp_path}': {unlink_err}")
            resume_parsing_time = time.perf_counter() - start_parse
        except Exception as parse_err:
            logger.error(f"Failed to parse resume: {parse_err}", exc_info=True)
            # Graceful warning: do not fail entirely, just proceed without resume text
            resume_text = ''
            logger.info("Proceeding without resume content due to parsing failure.")

    profile_text = build_profile_text([education, skills, experience, desired_roles, resume_text])
    if not profile_text:
        logger.warning("Request rejected: Empty profile builder content.")
        raise HTTPException(status_code=400, detail='Please provide at least one skill, experience, education, or resume content.')

    logger.info(f"Combined profile text size: {len(profile_text)} characters.")

    # Model Embeddings
    try:
        logger.info("Step 3/5: Generating embedding vector from profile text...")
        student_embedding = generate_embedding(profile_text)
        logger.info(f"Embedding generated. Vector length: {len(student_embedding)}")
    except Exception as emb_err:
        logger.error(f"Embedding generation failed: {emb_err}", exc_info=True)
        student_embedding = [0.0] * 384
        logger.info("Defaulting to a zero-vector embedding to prevent workflow failure.")

    # Aggregating
    aggregation_time = 0.0
    try:
        logger.info("Step 4/5: Running aggregator to search and ingest live engineering jobs...")
        start_agg = time.perf_counter()
        search_query = desired_roles or skills or 'software engineer'
        aggregator = JobAggregator()
        await aggregator.aggregate(db, query=search_query)
        aggregation_time = time.perf_counter() - start_agg
        logger.info("Aggregator run successfully executed.")
    except Exception as agg_err:
        logger.error(f"Aggregator encountered an error: {agg_err}", exc_info=True)
        logger.info("Aggregator failed. Proceeding with existing jobs in database.")

    # Matching
    matching_time = 0.0
    try:
        logger.info("Step 5/5: Running matcher to filter and score jobs...")
        start_match = time.perf_counter()
        matcher = JobMatcher(min_score=0.85)
        matched_jobs, is_fallback, message = matcher.find_matches(db, student_embedding, profile_text, page=page, limit=limit)
        matching_time = time.perf_counter() - start_match
        logger.info(f"Matcher returned {len(matched_jobs)} matches. Fallback active: {is_fallback}")
    except Exception as match_err:
        logger.error(f"Critical error during matching pipeline: {match_err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Job matching pipeline failed internally: {str(match_err)}")

    # Consolidated report
    logger.info(
        f"\n=============================================\n"
        f"=== REQUEST TIMING REPORT ===\n"
        f"Resume Parsing Stage: {resume_parsing_time:.3f} seconds\n"
        f"Job Aggregation Stage: {aggregation_time:.3f} seconds\n"
        f"Semantic Matching Stage: {matching_time:.3f} seconds\n"
        f"Total Pipeline Execution Time: {(resume_parsing_time + aggregation_time + matching_time):.3f} seconds\n"
        f"============================================="
    )

    logger.info("--- Request completed successfully. Returning recommendations. ---")
    return schemas.MatchResponse(
        student_id=student.id,
        matched_jobs=matched_jobs,
        is_fallback=is_fallback,
        message=message,
        meta=schemas.PaginationMeta(page=page, limit=limit, total_matches=len(matched_jobs))
    )

@app.post('/api/auth/register', response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Stub: Normally hash the password here using passlib
    fake_hashed_password = user.password + "notreallyhashed"
    return crud.create_user(db=db, email=user.email, hashed_password=fake_hashed_password, full_name=user.full_name)

@app.post('/api/auth/login')
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    # Stub: Normally verify password and generate JWT
    return {"access_token": "fake-jwt-token", "token_type": "bearer"}

@app.post('/api/jobs/{job_id}/apply')
def apply_to_job(job_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    # user_id should come from JWT token dependency
    app = crud.create_job_application(db, user_id, job_id)
    return {"status": "success", "application_id": app.id}

@app.get('/api/health')
def health_check():
    return {'status': 'ok', 'version': '2.0.0 (Production AI)'}

@app.get('/health')
def health_check_root():
    return {'status': 'ok'}

