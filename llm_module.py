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

def generate_poster_prompt_from_params(params: dict) -> dict:
    """
    Генерирует prompt для постера через Deepseek/OpenRouter на основе всех выбранных параметров wizard-а.
    """
    if not OPENROUTER_API_KEY:
        return {"error": "Генерация отключена: отсутствует ключ API."}

    prompt = (
        "Сгенерируй короткий, лаконичный prompt на английском для генератора изображений Kandinsky по следующим параметрам:\n"
    )
    for k, v in params.items():
        prompt += f"- {k}: {v}\n"
    prompt += (
        'Если выбран параметр "Без текста", обязательно явно укажи в prompt: "no text, no letters, no words, no typography". '
        'Не включай в prompt описание проекта, если пользователь просит убрать текст. '
        'Prompt должен быть понятен Kandinsky, без личных обращений, только перечисление нужных деталей. '
        'Ответ только в формате JSON: {"prompt": "...", "reason": "..."}'
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Ты — эксперт в генерации промптов для изображений. Отвечай только в формате чистого JSON-объекта без текста вне JSON."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "max_tokens": 2500
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        if response.status_code != 200:
            return {"error": f"Ошибка API: {response.status_code} - {response.text}"}

        resp_json = response.json()
        content = resp_json["choices"][0]["message"]["content"].strip()
        print("ОТВЕТ ОТ LLM:", content)

        # Удаляем markdown-обертку (```) если есть
        import re
        # Эта регулярка достает JSON внутри блока ```json ... ```
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        # Или просто ищем JSON-объект, если без markdown
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        return {"error": "Не удалось найти валидный JSON в ответе LLM."}
    except Exception as e:
        return {"error": f"Ошибка соединения: {e}"}