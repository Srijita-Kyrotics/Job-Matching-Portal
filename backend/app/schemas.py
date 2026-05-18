from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    education: Optional[str] = None
    skills: Optional[str] = None
    experience: Optional[str] = None
    desired_roles: Optional[str] = None

class MatchBreakdown(BaseModel):
    semantic_similarity: float
    skill_overlap_ratio: float
    matched_skills: List[str]
    missing_skills: List[str]

class JobPosting(BaseModel):
    id: Optional[int] = None
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    score: Optional[float] = None
    source: Optional[str] = None
    match_breakdown: Optional[MatchBreakdown] = None

class PaginationMeta(BaseModel):
    page: int
    limit: int
    total_matches: int

class MatchResponse(BaseModel):
    student_id: int
    matched_jobs: List[JobPosting]
    is_fallback: bool = False
    message: Optional[str] = None
    meta: Optional[PaginationMeta] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    
    class Config:
        orm_mode = True

