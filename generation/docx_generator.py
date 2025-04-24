import re
from .utils import parse_sections, summarize_text

def generate_docx(section_text: str, semantic: dict) -> dict:
    """
    Генерация блоков для .docx: краткое и подробное описание + теги
    """
    blocks = {}

    # 1) Очистка: удаляем ссылки и ненужные секции
    cleaned = re.sub(r'http\S+', '', section_text)
    ignore = [
        "Оглавление", "Содержание",
        "Список литературы", "Список источников",
        "Библиография", "Литература",
        "Источники", "Ссылки"
    ]
    names = '|'.join(re.escape(name) for name in ignore)
    # удаляем любые секции "Список литературы" и проч., 
    # как с любым количеством #, так и без них
    cleaned = re.sub(
        rf"(?im)^(?:\s*#+\s*)?(?:{names})[\s\S]*?(?=(?:^#+\s)|\Z)",
        "",
        cleaned
    )

    # 2) Парсим секции
    sections = parse_sections(cleaned)

    # 3) Краткое описание (раздел Введение или первые предложения)
    intro = next((sections[key] for key in sections if key.lower() == "введение"), "")
    if intro:
        try:
            summary_short = summarize_text(intro, max_length=90, min_length=50)
        except Exception:
            summary_short = ". ".join(intro.split('.')[:4]).strip() + '.'
    else:
        sentences = re.split(r'\.\s+', cleaned)
        summary_short = ". ".join(sentences[:4]).strip() + '.'
    blocks['short'] = summary_short

    # 4) Подробное описание
    desired = [
        ("Цель проекта", r"\bцель\w*\b"),
        ("Задачи проекта", r"\bзадач\w*\b"),
        ("Актуальность проекта", r"\bактуальн\w*\b"),
        ("Ожидаемый результат", r"\bрезультат\w*\b"),
    ]
    long_parts = []
    all_sentences = [p.strip() for p in re.split(r'\n\s*\n', cleaned) if p.strip()]
    for title, pattern in desired:
        text_block = None
        # ищем раздел по заголовку
        for sec_title, content in sections.items():
            if re.search(pattern, sec_title, re.IGNORECASE):
                text_block = content.strip()
                break
        # если нет — ищем предложения
        if not text_block:
            matches = [s.strip() for s in all_sentences if re.search(pattern, s, re.IGNORECASE)]
            if matches:
                text_block = ' '.join(matches)
        if not text_block:
            continue

        # для Задач и Актуальности возвращаем полный текст блока
        if title in ("Задачи проекта", "Актуальность проекта"):
            summary = text_block
        else:
            try:
                summary = summarize_text(text_block, max_length=200, min_length=80)
            except Exception:
                summary = ". ".join(text_block.split('.')[:2]).strip() + '.'

        long_parts.append(f"### {title}\n{summary.strip()}")
    blocks['long'] = "\n\n".join(long_parts)

    # 5) Теги
    blocks['tags'] = semantic.get('keywords', [])
    return blocks
