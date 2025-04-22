# Project Passport Generator

## Установка
conda create -n project3 python=3.12
conda activate project3
conda install gensim=4.3.3
conda install numpy spacy scikit-learn pillow sqlalchemy
pip install fastapi uvicorn pydantic python-docx python-pptx pymupdf rake-nltk yake nltk sumy python-multipart


1. Создайте виртуальное окружение:
   ```bash
   python3 -m venv venv
   venv\Scripts\activate

2. Установите зависимости:

Установите зависимости:
pip install -r requirements.txt

Скачайте модель spaCy (русский):
python -m spacy download ru_core_news_lg

Инициализируйте данные NLTK (для RAKE‑NLP):
python -c "import nltk; nltk.download('stopwords')"

Запуск
uvicorn app:app --reload

Сервис будет доступен по адресу http://127.0.0.1:8000/.

API
POST /api/projects/
Создать проект, тело { "name": "Название" } → { "project_id": 1 }

POST /api/projects/{id}/upload
Загрузить до 3 файлов (multipart/form-data, поле files) → { "status": "processing" }

GET /api/projects/{id}/status
Проверить статус: pending / processing / done

GET /api/projects/{id}/result
Когда статус=done, вернёт { summary_short, summary_long, tags }

Теперь вы можете локально загружать .docx, .pptx, .pdf, получать из них структурированный «паспорт проекта» и при необходимости редактировать его в своём фронтенде!