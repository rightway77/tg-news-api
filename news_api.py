from fastapi import FastAPI, Request, HTTPException, Response
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
        base_url = str(request.base_url).rstrip("/")

        if base_url and not base_url.startswith("http"):
           base_url = "https://" + base_url

    return [
        {
            "id": n["id"],
            "title": n["title"],
            "description": n["description"],
            "date": n["date_text"],
            "photos": [f"{base_url}/media/{file_id}" for file_id in n.get("photo_file_ids", [])],
        }
        for n in items
    ]

@app.get("/media/{file_id}")
def get_media(file_id: str):
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_TOKEN not set")

    info = requests.get(
        f"https://api.telegram.org/bot{bot_token}/getFile",
        params={"file_id": file_id},
        timeout=20,
    ).json()

    if not info.get("ok"):
        raise HTTPException(status_code=404, detail="file_id not found")

    file_path = info["result"]["file_path"]
    file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

    r = requests.get(file_url, timeout=30)
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="file not found")

    # определяем тип по расширению
    lower = file_path.lower()
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif lower.endswith(".png"):
        media_type = "image/png"
    elif lower.endswith(".webp"):
        media_type = "image/webp"
    else:
        # на всякий случай
        media_type = "image/jpeg"

    return Response(
        content=r.content,
        media_type=media_type,
        headers={
            # важно: никаких attachment
            "Cache-Control": "public, max-age=86400"
        },
    )