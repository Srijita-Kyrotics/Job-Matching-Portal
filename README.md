# Job Matching Portal

A structured job matching portal built with a full pipeline design:

Frontend (React)
  ↓
Backend API (FastAPI)
  ↓
AI Matching Engine
  ↓
Resume Parser + Embeddings
  ↓
Job Aggregator Service
  ↓
Database + Vector DB style storage

## What has been implemented

### Frontend
- React + Vite single-page application in `frontend/`
- Student intake form for:
  - name
  - email
  - education
  - skills
  - experience
  - desired roles
  - resume upload (`.pdf`, `.doc`, `.docx`, `.txt`)
- Submit form to `/api/match`
- Displays recommended jobs with score and URL link
- Safely renders job links only when valid URLs exist

### Backend
- FastAPI backend in `backend/app/main.py`
- SQLite persistence via SQLAlchemy in `backend/app/database.py`
- Student profiles stored in `backend/app/models.py`
- Job postings stored in `backend/app/models.py` with embeddings saved alongside each record
- Resume parser in `backend/app/services/resume_parser.py`
  - supports PDF, DOCX, and plain text
- Embedding generator in `backend/app/services/embeddings.py`
  - deterministic token-based embedding approximation
- Job aggregator in `backend/app/services/job_aggregator.py`
  - sample hardcoded job data
  - Indeed job scraping connector
  - persists jobs and their embeddings in SQLite
- Matching engine in `backend/app/services/matcher.py`
  - computes token overlap and embedding similarity
  - returns strict matches when found
  - falls back to top-ranked jobs when no strong matches exist
- Full match orchestration in `backend/app/main.py`
  - profile text + resume is embedded
  - jobs are aggregated and stored
  - matching logic returns ranked recommendations

## How to run

1. Backend
   - `cd backend`
   - `python -m venv .venv`
   - `.\.venv\Scripts\activate`
   - `pip install -r requirements.txt`
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

2. Frontend
   - `cd frontend`
   - `npm install`
   - `npm run dev`

3. Open the frontend URL shown by Vite (usually `http://localhost:5173`)

## Dependency and compatibility notes

- The backend dependencies were pinned and fixed for Windows/Python 3.14 compatibility
- `python-docx`, `PyPDF2`, `python-multipart`, `email-validator`, and `SQLAlchemy` were adjusted to avoid install/runtime issues
- This is now a working local prototype environment for the portal

## How to verify it is working

- Start the backend and frontend
- Submit the form with student details and optional resume
- The frontend will call `POST /api/match`
- The backend will:
  - store the student profile
  - parse resume text when uploaded
  - create a profile embedding from form + resume content
  - aggregate job postings and store them with embeddings
  - compute combined match scores
  - return recommended jobs with scores
- The frontend will:
  - display job cards with titles, companies, location, description, and score
  - open job links in a new browser tab when available

## AI / ML status

- The system now implements an AI-style matching pipeline:
  - deterministic text embeddings are generated from profile and job text
  - token overlap and embedding similarity are combined for ranking
- The match cutoff has been lowered to `0.6` to avoid empty recommendation sets during prototyping
- If no strict threshold matches exist, the top 5 closest jobs are returned
- This is still a prototype engine, not a production transformer or trained model
- For a real AI/ML pipeline, replace `backend/app/services/embeddings.py` with a real embedding model or API and use a dedicated vector database

## Production notes

- The current system follows the requested pipeline, but it remains a prototype implementation
- Important production improvements include:
  - official job APIs instead of scraping
  - authentication and authorization
  - persistent production-grade database
  - dedicated vector DB for embeddings
  - logging, metrics, monitoring, and scaling
  - Docker or cloud deployment
