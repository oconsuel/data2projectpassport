import re
import fitz         # PyMuPDF
import io
from PIL import Image
import pytesseract
from .utils import summarize_text, parse_sections

def ocr_extract_pdf(path: str) -> str:
    """
    Извлекает весь текст из PDF через OCR (pytesseract).
    """
    doc = fitz.open(path)
    pages = []
    for page in doc:
        # Рендерим страницу в 200 DPI для более точного OCR
        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        # Распознаём русский текст
        txt = pytesseract.image_to_string(img, lang="rus")
        pages.append(txt)
    doc.close()
    return "\n\n".join(pages)

def generate_pdf(path: str, semantic: dict) -> dict:
    """
    Генерация блоков для PDF: краткое и подробное описание + теги.
    Текст берётся через OCR, затем нормализуется и парсится секциями.
    """
    blocks = {}

    # 1) OCR-извлечение
    raw = ocr_extract_pdf(path)

    # 2) Очистка и нормализация заголовков
    text = re.sub(r'(?m)^##\s*Page\s*\d+\s*$', '', raw)
    text = re.sub(r'(?m)^\s*\d+\s*$', '', text)
    text = re.sub(r'\d+\.\.+|\d+\.\d+\.\.+', '', text)
    text = re.sub(r'http\S+', '', text)
    # «### Заголовок» → «## Заголовок»
    text = re.sub(r'(?m)^###\s*', '## ', text)
    # «1.2. Цель проекта» → «## Цель проекта»
    text = re.sub(r'(?m)^(?:##\s*)?\s*\d+(?:\.\d+)*\.\s*(.+)', r'## \1', text)

    # 3) Разбиение на абзацы и парсинг секций
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    sections = parse_sections(text)

    # 4) Краткое описание (Введение или первый длинный абзац)
    intro = sections.get("Введение", "")
    if not intro:
        for i, p in enumerate(paras):
            if re.match(r'^(?:##\s*)?Введение\b', p, re.IGNORECASE):
                j, parts = i+1, []
                while j < len(paras) and not re.match(r'^#+\s*|^- ', paras[j]):
                    parts.append(re.sub(r'^##\s*', '', paras[j]))
                    j += 1
                intro = " ".join(parts)
                break
    if not intro:
        long_paras = [
            p for p in paras
            if len(p.split()) > 15 and "ГБОУ" not in p
               and not re.match(r'^(Оглавление|Содержание)$', p, re.IGNORECASE)
        ]
        intro = long_paras[0] if long_paras else ""

    if intro:
        intro_clean = re.sub(r'^\s*Введение\b\s*', '', intro, flags=re.IGNORECASE)
        intro_clean = re.sub(r'\.\.+', '.', intro_clean)
        try:
            blocks['short'] = summarize_text(intro_clean, max_length=90, min_length=50)
        except Exception:
            sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', intro_clean) if s.strip()]
            blocks['short'] = ". ".join(sents[:3]) + ('.' if sents else '')
    else:
        blocks['short'] = "Краткое описание отсутствует."

    # 5) Подробное описание: ищем ключевые разделы
    desired = [
        ("Цель проекта",               r"Цель проекта"),
        ("Задачи проекта",             r"Задачи проекта|Задач"),
        ("Актуальность проекта",       r"Актуальн"),
        ("Перспективы развития проекта", r"Перспектив")
    ]
    long_parts = []
    for title, pat in desired:
        block = None
        # поиск по заголовкам секций
        for sec_title, content in sections.items():
            if re.search(pat, sec_title, re.IGNORECASE):
                block = content.strip()
                break
        # фоллбек — первый абзац, где встречается паттерн
        if not block:
            matches = [p for p in paras if re.search(pat, p, re.IGNORECASE)]
            block = matches[0] if matches else None
        if not block:
            continue

        if title in ("Задачи проекта", "Актуальность проекта"):
            summary = block
        else:
            try:
                summary = summarize_text(block, max_length=200, min_length=80)
            except Exception:
                sents = [s.strip() for s in block.split('.') if s.strip()]
                summary = ". ".join(sents[:2]) + ('.' if sents else '')

        long_parts.append(f"### {title}\n{summary.strip()}")

    blocks['long'] = "\n\n".join(long_parts) or "Подробное описание отсутствует."
    blocks['tags'] = semantic.get("keywords", [])

    return blocks
