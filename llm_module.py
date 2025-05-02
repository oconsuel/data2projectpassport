import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "deepseek/deepseek-r1"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def process_content(content: str) -> str:
    """Удаляет теги <think> и </think> из текста."""
    return content.replace('<think>', '').replace('</think>', '')

def generate_recommendations(summary_text: str, tags: list[str]) -> dict:
    if not OPENROUTER_API_KEY:
        return {"error": "Генерация отключена: отсутствует ключ API."}

    prompt = (
        f"На основе описания проекта: '{summary_text}' и ключевых слов: {', '.join(tags)}, "
        f"предложи улучшенную версию описания проекта в формате JSON. "
        f"Ответ должен быть чистым JSON-объектом, начинающимся с '{' и заканчивающимся '}', без префиксов или суффиксов. "
        f"Структура JSON должна включать следующие поля:\n"
        f"- summary_short: краткое описание проекта (максимум 100 слов, без Markdown).\n"
        f"- summary_short_reason: причина изменений в кратком описании.\n"
        f"- summary_long: подробное описание проекта, разделённое на 4 блока (Цель, Задачи, Актуальность, Ожидаемый результат), без Markdown, в виде объекта с полями goal, tasks, relevance, expected_result.\n"
        f"- summary_long_reason: причина изменений в подробном описании.\n"
        f"- tags: список тегов (короткие, релевантные ключевые слова).\n"
        f"- tags_reason: причина изменений в тегах.\n"
        f"Избегай использования Markdown (например, ###, -, *). Текст должен быть чистым, без лишних символов. "
        f"Пример JSON:\n"
        f'{{"summary_short": "Текст краткого описания", "summary_short_reason": "Причина изменений", '
        f'"summary_long": {{"goal": "Цель проекта", "tasks": "Задачи проекта", "relevance": "Актуальность проекта", "expected_result": "Ожидаемый результат"}}, '
        f'"summary_long_reason": "Причина изменений", "tags": ["тег1", "тег2"], "tags_reason": "Причина изменений"}}'
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Ты — эксперт в области проектного анализа. Отвечай только в формате чистого JSON-объекта без текста вне JSON."},
            {"role": "user", "content": prompt}
        ],
        "stream": True,
        "max_tokens": 2500
    }

    try:
        full_response = []
        with requests.post(OPENROUTER_API_URL, headers=headers, json=data, stream=True) as response:
            if response.status_code != 200:
                return {"error": f"Ошибка API: {response.status_code} - {response.text}"}

            for chunk in response.iter_lines():
                if chunk:
                    chunk_str = chunk.decode('utf-8').strip()
                    if chunk_str.startswith('data: '):
                        chunk_str = chunk_str[5:]  # Удаляем префикс 'data: '
                    if chunk_str == '[DONE]':  # OpenRouter может отправлять [DONE] в конце потока
                        break
                    try:
                        chunk_json = json.loads(chunk_str)
                        if "choices" in chunk_json:
                            content = chunk_json["choices"][0]["delta"].get("content", "")
                            if content:
                                cleaned = process_content(content)
                                full_response.append(cleaned)
                    except json.JSONDecodeError:
                        print(f"Невалидный чанк: {chunk_str}")
                        continue

        response_text = ''.join(full_response).strip()
        print(f"Собранный ответ: {response_text}")

        try:
            import re
            # Ищем JSON-объект в ответе
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                print(f"Найденный JSON: {json_str}")
                return json.loads(json_str)
            return {"error": "Не удалось найти валидный JSON в ответе API."}
        except json.JSONDecodeError as e:
            print(f"Ошибка разбора JSON: {e}, исходный текст: {response_text}")
            return {"error": f"Не удалось разобрать ответ API в JSON: {e}"}

    except Exception as e:
        print(f"Ошибка соединения: {e}")
        return {"error": f"Ошибка соединения: {e}"}

def generate_poster_prompt(summary: str, tags: list[str], user_comment: str) -> dict:
    """Генерирует новый промпт для постера на основе комментария пользователя."""
    if not OPENROUTER_API_KEY:
        return {"error": "Генерация отключена: отсутствует ключ API."}

    prompt = (
        f"Текущий постер создан на основе описания: '{summary}' и тегов: {', '.join(tags)}. "
        f"Пользователь оставил комментарий о том, что ему не нравится: '{user_comment}'. "
        f"Сгенерируй новый промпт для создания постера в формате JSON. "
        f"Ответ должен быть чистым JSON-объектом, начинающимся с '{' и заканчивающимся '}', без префиксов или суффиксов. "
        f"Структура JSON должна включать следующие поля:\n"
        f"- prompt: текстовый промпт для генерации постера (максимум 200 символов, без Markdown).\n"
        f"- reason: причина изменений в промпте, основанная на комментарии пользователя.\n"
        f"Избегай использования Markdown (например, ###, -, *). Текст должен быть чистым, без лишних символов. "
        f"Пример JSON:\n"
        f'{{"prompt": "Модерный постер с мягкими цветами", "reason": "Пользователь указал, что яркие цвета не подходят"}}'
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Ты — эксперт в дизайне и генерации изображений. Отвечай только в формате чистого JSON-объекта без текста вне JSON."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        with requests.post(OPENROUTER_API_URL, headers=headers, json=data, stream=True) as response:
            if response.status_code != 200:
                return {"error": f"Ошибка API: {response.status_code} - {response.text}"}

            full_response = []
            for chunk in response.iter_lines():
                if chunk:
                    chunk_str = chunk.decode('utf-8').replace('data: ', '')
                    try:
                        chunk_json = json.loads(chunk_str)
                        if "choices" in chunk_json:
                            content = chunk_json["choices"][0]["delta"].get("content", "")
                            if content:
                                cleaned = process_content(content)
                                full_response.append(cleaned)
                                print(f"Chunk: {cleaned}")  # Отладочный вывод
                    except json.JSONDecodeError:
                        print(f"Invalid chunk: {chunk_str}")  # Отладка невалидных фрагментов

            response_text = ''.join(full_response).strip()
            print(f"Raw response: {response_text}")  # Отладка полного ответа
            try:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    # Убедимся, что prompt не превышает 200 символов
                    if len(result.get("prompt", "")) > 200:
                        result["prompt"] = result["prompt"][:197] + "..."
                    return result
                return {"error": "Не удалось найти валидный JSON в ответе API."}
            except json.JSONDecodeError as e:
                return {"error": f"Не удалось разобрать ответ API в JSON: {e}"}

    except Exception as e:
        return {"error": f"Ошибка соединения: {e}"}