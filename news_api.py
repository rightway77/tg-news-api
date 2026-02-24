from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import requests
import os

from news_db import list_news
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/photo/{file_id}")
def get_photo(file_id: str):
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="BOT_TOKEN not set")

    # 1) getFile
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile", params={"file_id": file_id})
    data = r.json()
    if not data.get("ok"):
        raise HTTPException(status_code=404, detail="file_id not found")

    file_path = data["result"]["file_path"]

    # 2) redirect to real file url
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    return RedirectResponse(url=file_url)

@app.get("/news")
def get_news(request: Request):
    items = list_news(limit=50)

    base_url = os.getenv("BASE_URL")
    if not base_url:
        base_url = str(request.base_url).rstrip("/")  # например https://tg-news-api...app

    return [
        {
            "id": n["id"],
            "title": n["title"],
            "description": n["description"],
            "date": n["date_text"],
            "photos": [
                f"{base_url}/photo/{file_id}"
                for file_id in n.get("photo_file_ids", [])  # <-- ВАЖНО: проверь имя поля
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