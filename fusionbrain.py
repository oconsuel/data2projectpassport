import json
import time
import requests
import os
import base64
from dotenv import load_dotenv
import time  # Добавляем для временной метки

load_dotenv()

class FusionBrainAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_pipeline(self):
        response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, pipeline, images=1, width=576, height=1024):  # Изменили на 9:16 (576x1024)
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "style": "DEFAULT",
            "negativePromptDecoder": "bright colors, acidity, high contrast",
            "generateParams": {
                "query": f'{prompt}'
            }
        }

        data = {
            'pipeline_id': (None, pipeline),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/pipeline/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['result']['files']
            if data['status'] == 'FAIL':
                raise Exception("Image generation failed: " + data.get('errorDescription', 'Unknown error'))
            attempts -= 1
            time.sleep(delay)
        raise Exception("Image generation timed out")

def generate_project_poster(summary: str, tags: list[str], project_id: int) -> str:
    """Генерирует постер для проекта и возвращает путь к файлу."""
    api_key = os.getenv("FUSIONBRAIN_API_KEY", "YOUR_API_KEY")
    secret_key = os.getenv("FUSIONBRAIN_SECRET_KEY", "YOUR_SECRET_KEY")
    api = FusionBrainAPI('https://api-key.fusionbrain.ai/', api_key, secret_key)
    
    tags_str = ", ".join(tags)
    prompt = f"{summary}. Keywords: {tags_str}. A modern and visually appealing vertical poster design."
    
    pipeline_id = api.get_pipeline()
    uuid = api.generate(prompt, pipeline_id, images=1, width=576, height=1024)
    files = api.check_generation(uuid)
    if not files:
        raise Exception("No image generated")
    
    image_data = files[0]
    image_bytes = base64.b64decode(image_data)
    
    poster_dir = os.path.join("uploads", str(project_id), "poster")
    os.makedirs(poster_dir, exist_ok=True)
    
    # Используем временную метку для уникального имени файла
    timestamp = int(time.time())
    poster_filename = f"poster_{timestamp}.jpg"
    poster_path = os.path.join(poster_dir, poster_filename)
    with open(poster_path, "wb") as f:
        f.write(image_bytes)
    
    return poster_path