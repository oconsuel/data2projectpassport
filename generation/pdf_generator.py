from .utils import summarize_text

def generate_pdf(section_text: str, semantic: dict) -> dict:
    """
    Описание постранично + теги для pdf.
    """
    blocks = {}
    # Короткое: берем текст первых двух страниц
    pages = section_text.split("## Page")[1:3]
    flat = " ".join(pages)
    blocks['short'] = summarize_text(flat, max_length=90, min_length=50)

    # Подробное: весь текст
    blocks['long'] = section_text
    blocks['tags'] = semantic.get("keywords", [])
    return blocks