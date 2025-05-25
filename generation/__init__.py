import os
from .utils import split_by_file
from .docx_generator import generate_docx
from .pptx_generator import generate_pptx
from .pdf_generator import generate_pdf

def generate_blocks(raw_text: str, semantic: dict):
    """
    Разделяем объединённый markdown-текст по файлам и
    вызываем соответствующий генератор для каждого.
    Возвращает список: [(filename, {"short":…, "long":…, "tags":[…]}), …]
    """
    results = []
    for fname, section in split_by_file(raw_text):
        ext = os.path.splitext(fname)[1].lower().lstrip('.')
        if ext == 'docx':
            blocks = generate_docx(section, semantic)
        elif ext == 'pptx':
            blocks = generate_pptx(section, semantic)
        elif ext == 'pdf':
            blocks = generate_pdf(fname, semantic)
        else:
            continue
        results.append((fname, blocks))
    return results
