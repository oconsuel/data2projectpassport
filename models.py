from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import json
from datetime import datetime

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(String, default="created")
    created_at = Column(DateTime, default=datetime.utcnow)
    recommendations = Column(String)
    poster_path = Column(String)  # Путь к постеру

    files = relationship("ProjectFile", back_populates="project")
    passport = relationship("ProjectPassport", back_populates="project", uselist=False)

class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    filename = Column(String)
    file_type = Column(String)

    project = relationship("Project", back_populates="files")

class ProjectPassport(Base):
    __tablename__ = "project_passports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    summary_short = Column(String)
    summary_long = Column(String)
    tags = Column(String)

    project = relationship("Project", back_populates="passport")
    subfiles = relationship("ProjectPassportSubfile", back_populates="passport")

class ProjectPassportSubfile(Base):
    __tablename__ = "project_passport_subfiles"

    id = Column(Integer, primary_key=True, index=True)
    passport_id = Column(Integer, ForeignKey("project_passports.id"))  # Связь с ProjectPassport
    filename = Column(String)
    summary_short = Column(String)
    summary_long = Column(String)
    tags = Column(String)

    passport = relationship("ProjectPassport", back_populates="subfiles")