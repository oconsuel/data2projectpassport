import spacy

nlp = spacy.load("ru_core_news_lg")

def preprocess(text):
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return {"sentences": sentences, "entities": entities, "doc": doc}
