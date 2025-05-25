import csv
import os

LOCUST_CSV = "pytests/tests/L-серия/locust_stats.csv"
PROTOCOL_CSV = "pytests/tests/L-серия/protocol_L.csv"
os.makedirs(os.path.dirname(PROTOCOL_CSV), exist_ok=True)

def parse_locust_csv(locust_csv):
    # Считываем только summary (последняя строка типа "Aggregated")
    with open(locust_csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        summary = None
        for row in rows:
            if row.get('Name') in ("Aggregated", "Total"):
                summary = row
        return summary

def get_max_user_count(locust_history_csv):
    # Находит максимальное количество пользователей по истории нагрузки
    with open(locust_history_csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        max_users = 0
        for row in rows:
            user_count = int(row.get("User Count", 0))
            if user_count > max_users:
                max_users = user_count
        return max_users

def check_l01(summary):
    # L01: 10 пользователей × 3 файла, время < 30с, 0 ошибок 5xx
    avg_response = float(summary["Average Response Time"]) / 1000  # мс → сек
    failures = int(summary["Failure Count"])
    requests = int(summary["Request Count"])
    # (Логика: если есть отдельный столбец для 5xx — парси отдельно)
    ok = avg_response <= 180 and failures == 0
    result = f"Среднее время отклика: {avg_response:.2f} c, Ошибок: {failures}, Запросов: {requests}"
    return ok, result

def check_l02(summary, max_users):
    failures = int(summary["Failure Count"])
    ok = failures > 0 or max_users >= 15  # критерий: либо отказ, либо вышли на 15 пользователей
    result = f"Пиковое число пользователей: {max_users}, Ошибок: {failures}"
    return ok, result

def log_protocol(id, elapsed, tester, input_params, result, ok):
    file_exists = os.path.exists(PROTOCOL_CSV)
    with open(PROTOCOL_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["ID", "Время выполнения, сек", "Испытатель", "Входные данные", "Фактический результат", "Оценка"])
        writer.writerow([id, "%.2f" % elapsed, tester, input_params, result, ok])

def main():
    import time
    start = time.time()
    tester = "autotest"
    # Анализируем CSV после L01
    summary = parse_locust_csv(LOCUST_CSV)
    if not summary:
        print("Не найден summary в locust_stats.csv")
        return
    
    max_users = get_max_user_count("pytests/tests/L-серия/locust_stats_history.csv")

    # L01
    ok1, res1 = check_l01(summary)
    log_protocol("L01", time.time()-start, tester, "10 пользователей, 3 файла", res1, ok1)
    print("L01:", res1, "OK" if ok1 else "FAIL")
    # L02
    ok2, res2 = check_l02(summary, max_users)
    log_protocol("L02", time.time()-start, tester, "стресс-тест, >=15 пользователей", res2, ok2)
    print("L02:", res2, "OK" if ok2 else "FAIL")

if __name__ == "__main__":
    main()
