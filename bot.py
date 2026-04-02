import asyncio
import time
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# --- НАСТРОЙКИ ---
TOKEN = "8389025017:AAHoEJhU2saMWfP50pv_d6kbjuiv_GKIliE"
DB_NAME = "bot_data.db"
WEB_APP_URL = "https://avstrialtg-collab.github.io/Katahawebapp/"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

# РАЗРЕШАЕМ ДОСТУП САЙТУ (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WatchRequest(BaseModel):
    user_id: int
    movie_name: str
    file_id: str

# Инициализация базы
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, full_name TEXT, join_date INTEGER)")
        await db.commit()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (id, full_name, join_date) VALUES (?, ?, ?)", 
                         (message.from_user.id, message.from_user.full_name, int(time.time())))
        await db.commit()

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 ОТКРЫТЬ КАТАЛОГ", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])

    await message.answer(
        "Приветствую! Ты попал в <b>KATAHA ВОЗВРАЩЕНИЕ</b>\n\nНажми кнопку ниже для выбора фильма.",
        parse_mode="HTML",
        reply_markup=markup
    )

# API: Получение списка фильмов
@app.get("/movies")
async def get_movies():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT name, file_id FROM movies") as cursor:
                movies = await cursor.fetchall()
                return [dict(row) for row in movies]
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return []

# API: Отправка фильма пользователю
@app.post("/select_movie")
async def select_movie(req: WatchRequest):
    try:
        caption = f"<b>🍿 {req.movie_name.upper()}</b>\n<i>Приятного просмотра!</i>"
        await bot.send_video(req.user_id, video=req.file_id, caption=caption, parse_mode="HTML")
        return {"status": "ok"}
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        raise HTTPException(status_code=500, detail="Error sending video")

# Запуск
async def main():
    await init_db()
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
