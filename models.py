from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    files = relationship("ProjectFile", back_populates="project")
    passport = relationship("ProjectPassport", uselist=False, back_populates="project")

class ProjectFile(Base):
    __tablename__ = "project_files"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    filename = Column(String)
    file_type = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="files")

class ProjectPassport(Base):
    __tablename__ = "project_passports"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    summary_short = Column(Text)
    summary_long = Column(Text)
    tags = Column(Text)  # JSON‑строка
    project = relationship("Project", back_populates="passport")
