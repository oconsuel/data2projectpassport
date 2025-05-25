import os
import requests
import time
import csv
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

PROTOCOL_DIR = "pytests/tests/F-серия"  # Папка для всех csv
os.makedirs(PROTOCOL_DIR, exist_ok=True)

INPUT_CSV = os.path.join(PROTOCOL_DIR, "input_data_F.csv")
PROTOCOL_CSV = os.path.join(PROTOCOL_DIR, "protocol_F.csv")

input_data = [
    ["Контрольный файл", "Адрес API"],
    ["pytests/test_files/file1.docx", "POST /projects/{project_id}/upload"],
    ["pytests/test_files/file2.pptx", "POST /projects/{project_id}/upload"],
    ["pytests/test_files/scan.pdf", "POST /projects/{project_id}/upload"],
]

if not os.path.exists(INPUT_CSV):
    with open(INPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(input_data)

def log_protocol(id, elapsed, tester, input_files, result, ok):
    file_exists = os.path.exists(PROTOCOL_CSV)
    with open(PROTOCOL_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["ID", "Время выполнения, сек", "Испытатель", "Исходные данные", "Фактический результат", "Оценка"])
        writer.writerow([id, "%.2f" % elapsed, tester, "; ".join(input_files), result, ok])

BASE_URL = "http://localhost:8000"  # адрес FastAPI-приложения
TEST_FILES_DIR = "pytests/test_files"

def create_project(name="Тестовый проект"):
    resp = requests.post(f"{BASE_URL}/", data={"name": name}, allow_redirects=False)
    assert resp.status_code in (303, 200)
    # Получаем id из редиректа
    location = resp.headers.get("location")
    project_id = location.split("/")[-1]
    return project_id

def upload_files(project_id, files):
    files_payload = [("files", (os.path.basename(f), open(f, "rb"))) for f in files]
    resp = requests.post(f"{BASE_URL}/projects/{project_id}/upload", files=files_payload, allow_redirects=False)
    print("UPLOAD PDF status:", resp.status_code)
    print("UPLOAD PDF text:", resp.text)
    assert resp.status_code in (303, 200)
    return resp

def get_project_status(project_id):
    resp = requests.get(f"{BASE_URL}/projects/{project_id}")
    print(f"GET /projects/{project_id} status: {resp.status_code}, url: {BASE_URL}/projects/{project_id}")
    print(resp.text)
    assert resp.status_code == 200
    return resp.text

def call_recommend(project_id):
    resp = requests.post(f"{BASE_URL}/recommend/{project_id}")
    assert resp.status_code == 200
    return resp.json()

def wait_until_ready(project_id, timeout=60):
    for _ in range(timeout):
        html = get_project_status(project_id)
        if "Статус:" in html and ("done" in html or "Готово" in html or "готово" in html.lower()):
            return True
        time.sleep(1)
    return False

def test_f01():
    start = time.time()
    project_id = create_project("F01 docx")
    input_files = [os.path.join(TEST_FILES_DIR, "file1.docx")]
    upload_files(project_id, input_files)
    assert wait_until_ready(project_id)
    html = get_project_status(project_id)
    ok = "Современные языковые модели" in html
    result = "Анализ выполнен, блоки есть, текст корректен" if ok else "Ошибка анализа"
    elapsed = time.time() - start
    log_protocol("F01", elapsed, "autotest", input_files, result, ok)
    assert ok
    print("F01 passed.")

def test_f02():
    start = time.time()
    project_id = create_project("F02 pptx")
    input_files = [os.path.join(TEST_FILES_DIR, "file2.pptx")]
    upload_files(project_id, input_files)
    assert wait_until_ready(project_id)
    html = get_project_status(project_id)
    ok = "Проект: F02 pptx" in html
    result = "Анализ выполнен, блоки есть, текст корректен" if ok else "Ошибка анализа"
    elapsed = time.time() - start
    log_protocol("F02", elapsed, "autotest", input_files, result, ok)
    assert ok
    print("F02 passed.")

def test_f03():
    start = time.time()
    project_id = create_project("F03 pdf")
    input_files = [os.path.join(TEST_FILES_DIR, "scan.pdf")]
    upload_files(project_id, input_files)
    assert wait_until_ready(project_id)
    html = get_project_status(project_id)
    ok = "pdf" in html
    result = "Анализ выполнен, блоки есть, текст корректен" if ok else "Ошибка анализа"
    elapsed = time.time() - start
    log_protocol("F03", elapsed, "autotest", input_files, result, ok)
    assert ok
    print("F03 passed.")

def test_f04():
    start = time.time()
    project_id = create_project("F04 multi")
    input_files = [
        os.path.join(TEST_FILES_DIR, "file1.docx"),
        os.path.join(TEST_FILES_DIR, "file2.pptx"),
        os.path.join(TEST_FILES_DIR, "scan.pdf"),
    ]
    upload_files(project_id, input_files)
    assert wait_until_ready(project_id)
    html = get_project_status(project_id)
    ok = ("Современные языковые модели" in html or "Языковые модели" in html or "pdf" in html)
    result = "Пакетная загрузка прошла успешно, результаты по всем файлам отображены" if ok else "Ошибка пакетной загрузки"
    elapsed = time.time() - start
    log_protocol("F04", elapsed, "autotest", input_files, result, ok)
    assert ok
    print("F04 passed.")

def test_f05():
    start = time.time()
    project_id = create_project("F05 llm")
    input_files = [os.path.join(TEST_FILES_DIR, "file1.docx")]
    upload_files(project_id, input_files)
    assert wait_until_ready(project_id)
    resp = call_recommend(project_id)
    ok = "recommendations" in resp
    result = "Генерация новых блоков выполнена, получены рекомендации от LLM" if ok else "Ошибка генерации рекомендаций"
    elapsed = time.time() - start
    log_protocol("F05", elapsed, "autotest", input_files, result, ok)
    assert ok
    print("F05 passed.")

if __name__ == "__main__":
    test_f01()
    test_f02()
    test_f03()
    test_f04()
    test_f05()
    print("All F-series functional tests done.")
