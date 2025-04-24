from fastapi import FastAPI, File, UploadFile, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os, shutil

import crud, models, schemas, extraction, preprocessing, semantic_analysis
from generation import generate_blocks
from database import SessionLocal, engine

# create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# serve uploaded files (including extracted images) at /uploads/...
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

# dependency: get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def project_list(request: Request, db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    return templates.TemplateResponse("index.html", {"request": request, "projects": projects})

@app.post("/", response_class=HTMLResponse)
def create_project(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    proj = crud.create_project(db, name=name)
    return RedirectResponse(f"/projects/{proj.id}", status_code=303)

@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(request: Request, project_id: int, db: Session = Depends(get_db)):
    proj = crud.get_project(db, project_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    passport = crud.get_passport(db, project_id)
    return templates.TemplateResponse("project_detail.html", {"request": request, "project": proj, "passport": passport})

@app.post("/projects/{project_id}/upload", response_class=HTMLResponse)
async def upload_files(
    request: Request,
    project_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    proj = crud.get_project(db, project_id)
    if not proj:
        raise HTTPException(404, "Project not found")

    # save uploaded docs
    project_dir = os.path.join("uploads", str(project_id))
    os.makedirs(project_dir, exist_ok=True)
    paths = []
    for uf in files:
        dest = os.path.join(project_dir, uf.filename)
        with open(dest, "wb") as buf:
            shutil.copyfileobj(uf.file, buf)
        crud.save_file(db, project_id, filename=uf.filename, file_type=uf.content_type)
        paths.append(dest)

    # extraction → preprocessing → semantic → generation
    text = extraction.extract_text_and_images(paths, project_dir)
    prep = preprocessing.preprocess(text)
    sem = semantic_analysis.semantic_analysis(prep)

    # generate blocks per file and select first
    file_blocks = generate_blocks(text, sem)
    first_name, first_blocks = file_blocks[0]
    short = first_blocks["short"]
    long_ = first_blocks["long"]
    tags = first_blocks["tags"]

    # save passport and mark done
    crud.save_passport(db, project_id, summary_short=short, summary_long=long_, tags=tags)
    crud.update_status(db, project_id, status="done")

    return RedirectResponse(f"/projects/{project_id}", status_code=303)