from .utils import summarize_text, parse_sections

def generate_pptx(section_text: str, semantic: dict) -> dict:
    """
    Объединённое слайдовое описание + теги для pptx.
    """
    blocks = {}
    # Короткое: суммируем весь текст
    flat = " ".join(section_text.splitlines())
    blocks['short'] = summarize_text(flat, max_length=90, min_length=50)

    # Подробное: сохраняем все разделы
    sections = parse_sections(section_text)
    long_parts = [f"## {title}\n{content}" for title, content in sections.items()]
    blocks['long'] = "\n\n".join(long_parts)

    blocks['tags'] = semantic.get("keywords", [])
    return blocks
