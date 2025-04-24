import re
# Summarization: try transformers, fallback to sumy
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


def parse_sections(text: str) -> dict[str, str]:
    """
    Разбирает текст, разделённый Markdown-заголовками '##',
    и возвращает словарь {section_title: content}.
    """
    sections: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s*(.+)", line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
        elif current:
            sections[current].append(line)
    return {title: "\n".join(lines).strip() for title, lines in sections.items()}


def split_by_file(raw_text: str):
    """
    Из объединённого текста выделяем сегменты по файлам:
      ---\n# filename.ext\n---\n<content>
    """
    pattern = r"---\n# ([^\n]+)\n---\n"
    parts = re.split(pattern, raw_text)
    it = iter(parts[1:])
    for fname, text in zip(it, it):
        yield fname, text