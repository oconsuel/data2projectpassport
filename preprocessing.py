import spacy

nlp = spacy.load("ru_core_news_lg")

def preprocess(text):
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return {"sentences": sentences, "entities": entities, "doc": doc}


{
    "keywords": ["платформа", "обучение", "школьник", "мобильный", "данные", ...],
    "topics": [
        "(0) 0.16*обучение + 0.10*платформа + 0.08*школьник + ...",
        "(1) 0.14*приложение + 0.11*мобильный + 0.07*интерфейс + ...",
        "(2) 0.12*данные + 0.10*анализ + 0.06*алгоритм + ..." 
    ],
    "goal_text": "Повысить доступность качественного учебного контента для школьников в рамках смешанного обучения.",
    "tasks_text": "Разработать онлайн-платформу; Создать мобильное приложение; Апробировать систему на базе пилотных школ.",
    "tech_keywords": ["Python", "Django", "Android"]
}
