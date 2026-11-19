"""Database setup and ORM models for the PR Understanding Copilot.
Uses SQLAlchemy with the SQLite URL from ``backend.config.settings``.
The models are deliberately simple – they capture the core entities needed for
assessment, questions, answers, evaluations and reports.
"""

from __future__ import annotations

import datetime as dt
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from ..config.settings import settings

# ---------------------------------------------------------------------------
# Engine and session
# ---------------------------------------------------------------------------
engine = create_engine(settings.sqlite_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()

# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------
class Intern(Base):
    __tablename__ = "interns"
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, unique=True, nullable=False, doc="A stable intern ID (e.g., email or username)")
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    assessments = relationship("Assessment", back_populates="intern")

class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    intern_id = Column(Integer, ForeignKey("interns.id"), nullable=False)
    repo_url = Column(String, nullable=False)
    pr_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    # JSON blobs for storing the original PR and diff context (optional)
    pr_metadata = Column(Text, nullable=True)
    diff_context = Column(Text, nullable=True)
    intern = relationship("Intern", back_populates="assessments")
    questions = relationship("QuestionRecord", back_populates="assessment", cascade="all, delete-orphan")
    report = relationship("ReportRecord", uselist=False, back_populates="assessment", cascade="all, delete-orphan")

class QuestionRecord(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    text = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    evidence = Column(Text, nullable=True)  # JSON string of evidence objects
    expected_concepts = Column(Text, nullable=True)  # JSON list of strings
    assessment = relationship("Assessment", back_populates="questions")
    answer = relationship("AnswerRecord", uselist=False, back_populates="question", cascade="all, delete-orphan")

class AnswerRecord(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=dt.datetime.utcnow)
    question = relationship("QuestionRecord", back_populates="answer")
    evaluation = relationship("EvaluationRecord", uselist=False, back_populates="answer", cascade="all, delete-orphan")

class EvaluationRecord(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False)
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=False)
    missing_concepts = Column(Text, nullable=True)  # JSON list
    misconceptions = Column(Text, nullable=True)   # JSON list
    follow_up_question = Column(Text, nullable=True)
    uncertainty = Column(Boolean, default=False)
    answer = relationship("AnswerRecord", back_populates="evaluation")

class ReportRecord(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    generated_at = Column(DateTime, default=dt.datetime.utcnow)
    content = Column(Text, nullable=False)  # Serialized JSON or markdown report
    assessment = relationship("Assessment", back_populates="report")

# ---------------------------------------------------------------------------
# Helper to create tables
# ---------------------------------------------------------------------------
def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

# Expose a convenient context manager for sessions
from contextlib import contextmanager

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
