from .utils import summarize_text, parse_sections
import inspect
import re
import logging

logging.basicConfig(level=logging.DEBUG)

def filter_context_text(text):
    """Фильтрует текст, исключая строки с ключевыми терминами."""
    irrelevant_keywords = ['цель', 'задач', 'актуальн', 'результат', 'проект', 'создание']
    lines = text.split('\n')
    filtered_lines = [
        line for line in lines
        if not any(kw in line.lower() for kw in irrelevant_keywords)
    ]
    return ' '.join(filtered_lines).strip()

def filter_tags(tags):
    """Фильтрует теги, убирая нерелевантные слова."""
    stop_words = ['гбоу', 'анна', 'школа']
    return [t for t in tags if t.lower() not in stop_words and len(t) > 3]

def generate_pptx(section_text: str, semantic: dict) -> dict:
    blocks = {}

    # 1) Разбиваем на слайды
    parts = re.split(r"^##\s*Slide (\d+)\s*$", section_text, flags=re.MULTILINE)
    nums = parts[1::2]
    conts = parts[2::2]
    slides = {int(n): c for n, c in zip(nums, conts)}
    logging.debug(f"Slides: {slides}")

    # 2) Краткое описание (без ключевых терминов)
    raw = " ".join(slides[i] for i in sorted(slides) if i != 1)
    clean = re.sub(r"(?m)^#+\s*", "", raw)
    clean = re.sub(r"(?m)^---.*?---\s*", "", clean)
    context_text = filter_context_text(clean)
    
    if context_text:
        try:
            blocks['short'] = summarize_text(context_text, max_length=90, min_length=50)
        except Exception as e:
            logging.error(f"Summarization failed: {e}")
            blocks['short'] = "Не удалось составить краткое описание."
    else:
        blocks['short'] = "Проект посвящён разработке решения для подбора дизайна маникюра."
    logging.debug(f"Short summary: {blocks['short']}")

    # 3) Подробное описание (чёткое разделение цели и задач)
    desired = [
        ("Цель", r"\bцель\w*\b"),
        ("Задачи", r"\bзадач\w*\b"),
        ("Актуальность", r"\bактуальн\w*\b"),
        ("Результаты", r"\bрезультат\w*\b"),
    ]
    long_parts = []
    used_nums = set()
    for title, patt in desired:
        for num in sorted(slides):
            if num not in used_nums and re.search(patt, slides[num], re.IGNORECASE):
                long_parts.append(f"### {title}\n{slides[num].strip()}")
                used_nums.add(num)
                break

    blocks['long'] = "\n\n".join(long_parts)
    blocks['tags'] = semantic.get("keywords", [])

    return blocks