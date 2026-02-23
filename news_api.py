from fastapi import FastAPI
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
            "title": n["title"],
            "description": n["description"],
            "date": n["date_text"],
        }
        for n in items
    ]