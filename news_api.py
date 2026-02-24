from fastapi import FastAPI, Response
import requests
import os
from fastapi.middleware.cors import CORSMiddleware

from news_db import list_news

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/news")
def get_news():
    items = list_news(limit=50)
    return [
    {
        "id": n["id"],
        "title": n["title"],
        "description": n["description"],
        "date": n["date_text"],
        "photos": [
            f"{os.getenv('BASE_URL')}/media/{file_id}"
            for file_id in n.get("photos", [])
        ],
    }
    for n in items
]

@app.get("/media/{file_id}")
def get_media(file_id: str):
    bot_token = os.getenv("BOT_TOKEN")

    # получаем путь к файлу
    file_info = requests.get(
        f"https://api.telegram.org/bot{bot_token}/getFile",
        params={"file_id": file_id},
    ).json()

    file_path = file_info["result"]["file_path"]

    # скачиваем файл
    file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    file_response = requests.get(file_url)

    return Response(
        content=file_response.content,
        media_type="image/jpeg"
    )