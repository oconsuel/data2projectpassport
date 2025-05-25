import os
import csv
import time
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем нужные модули и функции
import extraction
import preprocessing
from llm_module import generate_recommendations

# Настройки
PROTOCOL_CSV = "pytests/tests/I-серия/protocol_I.csv"
os.makedirs(os.path.dirname(PROTOCOL_CSV), exist_ok=True)

def log_protocol(id, elapsed, tester, input_files, result, ok):
    file_exists = os.path.exists(PROTOCOL_CSV)
    with open(PROTOCOL_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["ID", "Время выполнения, сек", "Испытатель", "Исходные данные", "Фактический результат", "Оценка"])
        writer.writerow([id, "%.2f" % elapsed, tester, "; ".join(input_files), result, ok])

def count_symbol_loss(original_text, processed_text):
    orig = len(original_text)
    proc = len(processed_text)
    lost = max(orig - proc, 0)
    percent = (lost / orig * 100) if orig else 0
    return percent

def test_i01():
    """I01: Сквозное извлечение + препроцессинг docx"""
    start = time.time()
    tester = "autotest"
    # Путь к docx-файлу для теста (замени на свой, если другой)
    docx_path = "pytests/test_files/file1.docx"
    project_dir = "pytests/test_files/tmp_project"
    project_id = 9999  # Тестовый ID (можно любой, т.к. БД не важна)
    db = None  # Если требуется, подставь тестовый объект БД

    # 1. Извлечение текста
    text = extraction.extract_text_and_images([docx_path], project_dir, project_id, db)
    orig_len = len(text)
    # 2. Препроцессинг
    prep = preprocessing.preprocess(text)
    processed_text = " ".join(prep.get("sentences", []))
    proc_len = len(processed_text)
    # 3. Оценка потери символов
    symbol_loss = count_symbol_loss(text, processed_text)
    ok = symbol_loss <= 5
    result = f"Потеря символов: {symbol_loss:.2f} % (исходный текст: {orig_len} символов, обработанный: {proc_len})"
    elapsed = time.time() - start
    log_protocol("I01", elapsed, tester, [docx_path], result, ok)
    print("I01 result:", result, "OK" if ok else "FAIL")

def test_i02():
    """I02: Генерация описания проекта через LLM"""
    start = time.time()
    tester = "autotest"
    # Минимальные входные данные
    summary_text = ""  # Пустая цель
    tags = []          # Нет тегов (или можно ["тест", "интеграция"])
    # 1. Вызов генерации через LLM
    recommendations = generate_recommendations(summary_text, tags)
    # 2. Проверка результата
    ok = False
    if recommendations and "summary_short" in recommendations and recommendations["summary_short"].strip():
        ok = True
        result = f"Рекомендация сгенерирована: {recommendations['summary_short'][:50]}..."
    else:
        result = f"Ошибка генерации: {recommendations.get('error', 'нет текста')}"
    elapsed = time.time() - start
    log_protocol("I02", elapsed, tester, ["summary_text='', tags=[]"], result, ok)
    print("I02 result:", result, "OK" if ok else "FAIL")

if __name__ == "__main__":
    test_i01()
    test_i02()
    print("All I-series integration tests done.")
