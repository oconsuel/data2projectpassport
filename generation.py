import re
from typing import Dict, List, Tuple

# попытка импортировать transformers, иначе fallback на sumy
try:
    from transformers import pipeline
    summarizer = pipeline(
        "summarization",
        model="IlyaGusev/rut5-base-sum-cnndm",
        device=-1
    )
    def summarize_text(text: str, max_length: int = 120, min_length: int = 30) -> str:
        result = summarizer(
            text, max_length=max_length, min_length=min_length, do_sample=False
        )
        return result[0]["summary_text"].strip()
except ImportError:
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.text_rank import TextRankSummarizer

    def summarize_text(text: str, sentence_count: int = 3) -> str:
        parser = PlaintextParser.from_string(text, Tokenizer("russian"))
        summarizer = TextRankSummarizer()
        summary = summarizer(parser.document, sentence_count)
        return " ".join(str(s) for s in summary)


def parse_sections(text: str) -> Dict[str, str]:
    """
    Разбирает текст, разделённый Markdown-заголовками '##', 
    и возвращает словарь {section_title: content}.
    """
    sections: Dict[str, List[str]] = {}
    current_title = None
    for line in text.splitlines():
        header_match = re.match(r"^##\s*(.+)", line)
        if header_match:
            current_title = header_match.group(1).strip()
            sections[current_title] = []
        elif current_title:
            sections[current_title].append(line)
    # объединяем строки разделов в единый текст
    return {title: "\n".join(lines).strip() for title, lines in sections.items()}


def generate_blocks(text: str, semantic: dict) -> Tuple[str, str, List[str]]:
    # Парсим текст на разделы
    sections = parse_sections(text)

    # 1) Краткое описание: берем вводный раздел 'Введение'
    intro_text = sections.get("Введение", "")
    if intro_text:
        try:
            # 3-4 предложения
            summary_short = summarize_text(intro_text, max_length=90, min_length=50)
        except Exception:
            # простое обрезание
            summary_short = ". ".join(intro_text.split('.')[:4]).strip() + '.'
    else:
        summary_short = ""

    # 2) Подробное описание: только Цель, Задачи, Актуальность проекта, Ожидаемый проектный результат
    desired = [
        ("Цель проекта", r"цель"),
        ("Задачи проекта", r"задач"),
        ("Актуальность проекта", r"актуальн"),
        ("Ожидаемый проектный результат", r"результат")
    ]
    long_parts = []
    for title, pattern in desired:
        # ищем секцию, где title содержит ключ
        for sec_title, content in sections.items():
            if re.search(pattern, sec_title, re.IGNORECASE):
                long_parts.append(f"### {title}\n{content}")
                break
    summary_long = "\n\n".join(long_parts)

    # 3) Теги из semantic_analysis
    raw_tags = semantic.get("keywords", [])
    tags = [w for w in raw_tags if w.isalpha() and len(w) > 2]

    return summary_short, summary_long, tags
