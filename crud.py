from sqlalchemy.orm import Session
from models import Project, ProjectFile, ProjectPassport, ProjectPassportSubfile
import json

def create_project(db: Session, name: str):
    proj = Project(name=name)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj

def get_project(db: Session, project_id: int):
    return db.query(Project).filter(Project.id == project_id).first()

def update_status(db: Session, project_id: int, status: str):
    proj = get_project(db, project_id)
    if proj:
        proj.status = status
        db.commit()
    return proj

def save_file(db: Session, project_id: int, filename: str, file_type: str):
    file = ProjectFile(project_id=project_id, filename=filename, file_type=file_type)
    db.add(file)
    db.commit()
    db.refresh(file)
    return file

def save_passport(db: Session, project_id: int, summary_short: str, summary_long: str, tags: list):
    tags_str = json.dumps(tags, ensure_ascii=False)
    passport = db.query(ProjectPassport).filter(ProjectPassport.project_id == project_id).first()
    if passport:
        passport.summary_short = summary_short
        passport.summary_long = summary_long
        passport.tags = tags_str
    else:
        passport = ProjectPassport(
            project_id=project_id,
            summary_short=summary_short,
            summary_long=summary_long,
            tags=tags_str,
        )
        db.add(passport)
    db.commit()
    db.refresh(passport)
    return passport

def get_passport(db: Session, project_id: int):
    return db.query(ProjectPassport).filter(ProjectPassport.project_id == project_id).first()

def save_passport_subfile(db: Session, project_id: int, filename: str,
                          summary_short: str, summary_long: str, tags: list):
    tags_str = json.dumps(tags, ensure_ascii=False)
    sub = ProjectPassportSubfile(
        project_id=project_id,
        filename=filename,
        summary_short=summary_short,
        summary_long=summary_long,
        tags=tags_str
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

def get_passport_subfiles(db: Session, project_id: int):
    return (db.query(ProjectPassportSubfile)
              .filter(ProjectPassportSubfile.project_id==project_id)
              .all())
