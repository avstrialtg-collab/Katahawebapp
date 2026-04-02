import asyncio
import time
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from fastapi import FastAPI
import uvicorn

# --- НАСТРОЙКИ ---
TOKEN = "8318172496:AAEy7qjJa-lQZW50Js6CKjLTieo2u8SrmPw"
DB_NAME = "bot_data.db"
# Твоя ссылка на GitHub Pages
WEB_APP_URL = "https://avstrialtg-collab.github.io/Katahawebapp/"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

# База данных
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
        "Приветствую! Ты попал к нам в логово: <b>KATAHA ВОЗВРАЩЕНИЕ</b>\n\n"
        "Нажми на кнопку ниже, чтобы запустить приложение.",
        parse_mode="HTML",
        reply_markup=markup
    )

# API для сайта (чтобы он видел фильмы)
@app.get("/movies")
async def get_movies():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM movies") as cursor:
            movies = await cursor.fetchall()
            return [dict(row) for row in movies]

# Запуск
async def main():
    await init_db()
    # Запускаем веб-сервер для WebApp в фоне
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    loop = asyncio.get_event_loop()
    loop.create_task(server.serve())
    
    # Запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
