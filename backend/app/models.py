from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(180), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profiles = relationship("SavedProfile", back_populates="user")
    applications = relationship("JobApplication", back_populates="user")

class SavedProfile(Base):
    __tablename__ = 'saved_profiles'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(120), nullable=False)
    education = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    desired_roles = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="profiles")

class Student(Base):
    __tablename__ = 'students'
    # Keeping for backward compatibility or guest users
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(180), nullable=False)
    education = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    desired_roles = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JobPosting(Base):
    __tablename__ = 'job_postings'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(260), nullable=False)
    company = Column(String(180), nullable=True)
    location = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=False, unique=True, index=True)
    source = Column(String(120), nullable=True)
    embedding = Column(Text, nullable=True)
    date_posted = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    applications = relationship("JobApplication", back_populates="job")

class JobApplication(Base):
    __tablename__ = 'job_applications'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    job_id = Column(Integer, ForeignKey('job_postings.id'))
    status = Column(String(50), default="Applied") # Applied, Interviewing, Rejected, Offer
    applied_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="applications")
    job = relationship("JobPosting", back_populates="applications")
