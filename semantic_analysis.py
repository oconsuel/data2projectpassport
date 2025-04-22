import spacy
from collections import Counter
from gensim import corpora, models

# загрузка spaCy один раз
nlp = spacy.load("ru_core_news_lg")

def extract_keywords(sentences, top_n=20):
    """
    Извлекаем ключевые слова (существительные и собственные имена) на основе частоты.
    """
    text = " ".join(sentences)
    doc = nlp(text)
    tokens = [
        tok.lemma_.lower() for tok in doc
        if tok.pos_ in ("NOUN", "PROPN") and tok.is_alpha and len(tok.lemma_) > 2
    ]
    freq = Counter(tokens)
    return [k for k, _ in freq.most_common(top_n)]

def extract_topics(sentences, num_topics=3):
    tokenized = [s.split() for s in sentences]
    dct = corpora.Dictionary(tokenized)
    corpus = [dct.doc2bow(t) for t in tokenized]
    lda = models.LdaModel(corpus=corpus, id2word=dct, num_topics=num_topics, passes=5)
    return lda.print_topics()

def semantic_analysis(prep):
    """
    Объединяет ключевые слова и темы в результат анализа.
    """
    sents = prep.get("sentences", [])
    return {
        "keywords": extract_keywords(sents),
        "topics": extract_topics(sents)
    }
