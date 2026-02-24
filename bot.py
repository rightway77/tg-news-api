import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

from news_db import init_db, add_news, list_news

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# --- Состояния диалога (шаги добавления новости) ---
class AddNews(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_date = State()

# --- Кнопки ---
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить новость")],
        [KeyboardButton(text="📰 Показать ленту")]
    ],
    resize_keyboard=True
)

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Привет! Этот бот работает только для администратора.")
        return
    await message.answer(
        "Привет! Я бот для управления лентой новостей.\n"
        "Выбери действие кнопкой ниже:",
        reply_markup=kb
    )

@dp.message(F.text == "➕ Добавить новость")
async def add_news_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddNews.waiting_title)
    await message.answer("Введи *заголовок* новости:", parse_mode="Markdown")

@dp.message(AddNews.waiting_title)
async def add_news_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddNews.waiting_description)
    await message.answer("Теперь введи *описание* новости:", parse_mode="Markdown")

@dp.message(AddNews.waiting_description)
async def add_news_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AddNews.waiting_date)
    await message.answer(
        "Теперь введи *дату* (например: 23.02.2026 или 2026-02-23):",
        parse_mode="Markdown"
    )

@dp.message(AddNews.waiting_date)
async def add_news_date(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data["title"]
    description = data["description"]
    date_text = message.text.strip()

    new_id = add_news(title=title, description=description, date_text=date_text)
    await state.clear()

    await message.answer(
        f"✅ Новость добавлена (ID: {new_id}).\n\n"
        f"*{title}*\n{description}\n📅 {date_text}",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.message(F.text == "📰 Показать ленту")
async def show_feed(message: Message):
    if not is_admin(message.from_user.id):
        return

    items = list_news(limit=10)
    if not items:
        await message.answer("Пока новостей нет. Нажми «Добавить новость».", reply_markup=kb)
        return

    text = "📰 *Лента новостей:*\n\n"
    for n in items:
        text += f"• *{n['title']}*\n{n['description']}\n📅 {n['date_text']}\n\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
