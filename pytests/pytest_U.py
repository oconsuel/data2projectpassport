import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import csv
from datetime import datetime
import os
from preprocessing import preprocess
from extraction import extract_from_docx
from docx import Document
import time


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

TEST_CORPUS_PATH = "pytests/test_files/test_corpus/test_corpus.json"
EXPECTED_HEADINGS_PATH = "pytests/test_files/test_corpus/doc_demo_expected.json"
DOCX_PATH = "pytests/test_files/file1.docx"
PROTOCOL_PATH = "pytests/tests/U-серия/protocol_U.csv"

os.makedirs(os.path.dirname(PROTOCOL_PATH), exist_ok=True)

def precision_recall(true, pred):
    true_set = set((e[0], e[1]) for e in true)
    pred_set = set((e[0], e[1]) for e in pred)
    tp = len(true_set & pred_set)
    precision = tp / len(pred_set) if pred_set else 1
    recall = tp / len(true_set) if true_set else 1
    return precision, recall

def run_ner_test():
    with open(TEST_CORPUS_PATH, encoding="utf-8") as f:
        corpus = json.load(f)
    all_precisions, all_recalls = [], []
    for item in corpus:
        res = preprocess(item["text"])
        precision, recall = precision_recall(item["entities"], res["entities"])
        all_precisions.append(precision)
        all_recalls.append(recall)
    avg_precision = sum(all_precisions) / len(all_precisions)
    avg_recall = sum(all_recalls) / len(all_recalls)
    passed = avg_precision >= 0.9 and avg_recall >= 0.9
    return {
        "id": "U-NER-01",
        "input": TEST_CORPUS_PATH,
        "result": f"precision: {avg_precision:.2f}, recall: {avg_recall:.2f}",
        "passed": passed
    }

def extract_headings_from_docx(docx_path):
    doc = Document(docx_path)
    headings = []
    for p in doc.paragraphs:
        style = (p.style.name or "").lower()
        if style.startswith("toc"):
            txt = p.text.strip()
            if txt:
                headings.append(txt)
    return headings

def run_extr_test():
    with open(EXPECTED_HEADINGS_PATH, encoding="utf-8") as f:
        expected = json.load(f)["headings"]
    actual = extract_headings_from_docx(DOCX_PATH)
    passed = actual == expected
    result = f"expected={expected}, actual={actual}"
    return {
        "id": "U-EXTR-01",
        "input": DOCX_PATH,
        "result": result,
        "passed": passed
    }

def main():
    results = []
    for test_func in (run_ner_test, run_extr_test):
        start = time.perf_counter()
        test = test_func()
        duration = time.perf_counter() - start
        results.append([
            test["id"],
            f"{duration:.2f}",
            test["input"],
            test["result"],
            "True" if test["passed"] else "False"
        ])
    # Сохраняем результаты
    with open(PROTOCOL_PATH, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ID теста", "Время выполнения, сек", "Входные данные", "Результат", "Оценка"])
        writer.writerows(results)
    print("Модульные тесты проведены. Протокол:", PROTOCOL_PATH)
    for row in results:
        print(row)

if __name__ == "__main__":
    main()
