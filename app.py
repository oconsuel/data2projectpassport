from fastapi import FastAPI, File, UploadFile, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os, shutil, json
import asyncio
import time

import crud, models, schemas, extraction, preprocessing, semantic_analysis
from generation import generate_blocks
from database import SessionLocal, engine
from fusionbrain import generate_project_poster

from models import Project, ProjectPassport
from llm_module import generate_recommendations, generate_poster_prompt
from crud import update_recommendations

# create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def generate_poster_async(project_id: int, summary: str, tags: list[str], db: Session):
    try:
        print(f"Starting poster generation for project {project_id}")
        poster_path = generate_project_poster(summary, tags, project_id)
        print(f"Poster generated at {poster_path}")
        crud.save_poster_path(db, project_id, poster_path)
        print(f"Poster path saved for project {project_id}")
    except Exception as e:
        print(f"Ошибка генерации постера для проекта {project_id}: {e}")

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
    tags = json.loads(passport.tags) if passport and passport.tags else []
    recommendations = json.loads(proj.recommendations) if proj.recommendations else None
    return templates.TemplateResponse(
        "project_detail.html",
        {
            "request": request,
            "project": proj,
            "passport": passport,
            "tags": tags,
            "recommendations": recommendations,
            "poster_loading": False
        }
    )

@app.post("/projects/{project_id}/upload", response_class=RedirectResponse)
async def upload_files(
    request: Request,
    project_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    proj = crud.get_project(db, project_id)
    if not proj:
        raise HTTPException(404, "Project not found")

    project_dir = os.path.join("uploads", str(project_id))
    os.makedirs(project_dir, exist_ok=True)
    paths = []
    for uf in files:
        dest = os.path.join(project_dir, uf.filename)
        with open(dest, "wb") as buf:
            shutil.copyfileobj(uf.file, buf)
        crud.save_file(db, project_id, filename=uf.filename, file_type=uf.content_type)
        paths.append(dest)

    text = extraction.extract_text_and_images(paths, project_dir, project_id, db)
    prep = preprocessing.preprocess(text)
    sem = semantic_analysis.semantic_analysis(prep)

    file_blocks = generate_blocks(text, sem)
    first_name, first_blocks = file_blocks[0]
    short = first_blocks["short"]
    long_ = first_blocks["long"]
    tags = first_blocks["tags"]

    passport = crud.save_passport(db, project_id, summary_short=short, summary_long=long_, tags=tags)

    crud.save_passport_subfile(db, passport_id=passport.id, filename=first_name,
                               summary_short=short, summary_long=long_, tags=tags)

    asyncio.create_task(generate_poster_async(project_id, short, tags, db))

    crud.update_status(db, project_id, status="done")

    return RedirectResponse(f"/projects/{project_id}", status_code=303)

@app.post("/recommend/{project_id}")
async def generate_llm_recommendations(project_id: int, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return {"error": "Проект не найден"}

    passport = db.query(ProjectPassport).filter(ProjectPassport.project_id == project_id).first()
    
    summary = passport.summary_short if passport and passport.summary_short else ""
    tags = json.loads(passport.tags) if passport and passport.tags else []

    recommendations = generate_recommendations(summary, tags)

    if "error" in recommendations:
        return {"error": recommendations["error"]}

    update_recommendations(db, project_id, json.dumps(recommendations, ensure_ascii=False))

    return {"recommendations": recommendations}

@app.get("/poster-status/{project_id}")
async def poster_status(project_id: int, db: Session = Depends(get_db)):
    proj = crud.get_project(db, project_id)
    timestamp = int(time.time())
    poster_path_with_timestamp = f"{proj.poster_path}?t={timestamp}" if proj.poster_path else None
    return JSONResponse({"poster_path": poster_path_with_timestamp})

@app.post("/regenerate-poster/{project_id}")
async def regenerate_poster(project_id: int, request: Request, db: Session = Depends(get_db)):
    proj = crud.get_project(db, project_id)
    if not proj:
        return JSONResponse({"error": "Проект не найден"}, status_code=404)

    passport = crud.get_passport(db, project_id)
    if not passport:
        return JSONResponse({"error": "Паспорт проекта не найден"}, status_code=404)

    data = await request.json()
    comment = data.get("comment")
    if not comment:
        return JSONResponse({"error": "Комментарий обязателен"}, status_code=400)

    summary = passport.summary_short if passport.summary_short else ""
    tags = json.loads(passport.tags) if passport.tags else []

    new_prompt_data = generate_poster_prompt(summary, tags, comment)

    if "error" in new_prompt_data:
        return JSONResponse({"error": new_prompt_data["error"]}, status_code=500)

    new_prompt_text = new_prompt_data.get("prompt", summary)
    new_tags = tags

    crud.save_poster_path(db, project_id, None)

    asyncio.create_task(generate_poster_async(project_id, new_prompt_text, new_tags, db))

    return JSONResponse({"status": "Генерация нового постера запущена"})