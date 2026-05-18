import json
from sqlalchemy.orm import Session
from . import models, schemas


def create_student(db: Session, student: schemas.StudentCreate):
    db_student = models.Student(
        name=student.name,
        email=student.email,
        education=student.education,
        skills=student.skills,
        experience=student.experience,
        desired_roles=student.desired_roles,
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def get_job_by_url(db: Session, url: str) -> models.JobPosting | None:
    return db.query(models.JobPosting).filter(models.JobPosting.url == url).first()


def create_job(db: Session, job_data: dict) -> models.JobPosting:
    embedding_value = job_data.get('embedding')
    if isinstance(embedding_value, list):
        embedding_text = json.dumps(embedding_value)
    else:
        embedding_text = embedding_value

    db_job = models.JobPosting(
        title=job_data['title'],
        company=job_data.get('company'),
        location=job_data.get('location'),
        description=job_data.get('description'),
        url=job_data['url'],
        source=job_data.get('source'),
        embedding=embedding_text,
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def list_jobs(db: Session) -> list[models.JobPosting]:
    return db.query(models.JobPosting).filter(models.JobPosting.is_active == True).all()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str, hashed_password: str, full_name: str = None):
    db_user = models.User(email=email, hashed_password=hashed_password, full_name=full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_job_application(db: Session, user_id: int, job_id: int):
    # Check if already applied
    existing = db.query(models.JobApplication).filter(
        models.JobApplication.user_id == user_id, 
        models.JobApplication.job_id == job_id
    ).first()
    if existing:
        return existing
        
    app = models.JobApplication(user_id=user_id, job_id=job_id)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app
