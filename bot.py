import asyncio
import time
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, FSInputFile
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class WatchRequest(BaseModel):
    user_id: int
    movie_name: str
    file_id: str

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, full_name TEXT, join_date INTEGER)")
        await db.commit()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (id, full_name, join_date) VALUES (?, ?, ?)", 
                         (message.from_user.id, message.from_user.full_name, int(time.time())))
        await db.commit()

    # Кнопка без стикеров, просто текст KATAHA
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="KATAHA", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])

    # Текст с кликабельной ссылкой
    text = (
        "Приветствую! Ты попал к нам в логово: <a href='https://t.me/der227'>KATAHA ВОЗВРАЩЕНИЕ</a>\n\n"
        "Нажми на кнопку ниже, чтобы запустить приложение."
    )
    
    try:
        # Убедись, что файл banner.jpg лежит в папке с ботом на GitHub
        banner = FSInputFile("banner.jpg")
        await message.answer_photo(photo=banner, caption=text, parse_mode="HTML", reply_markup=markup)
    except:
        await message.answer(text, parse_mode="HTML", reply_markup=markup)

@app.get("/movies")
async def get_movies():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT name, file_id, sum_rating, count FROM movies") as cursor:
            movies = await cursor.fetchall()
            return [dict(row) for row in movies]

@app.post("/select_movie")
async def select_movie(req: WatchRequest):
    try:
        # Формат как в bot1: Название (ссылка) + Моно-текст про удаление
        # Оценку убрали по просьбе
        movie_link = f"<a href='https://t.me/der227'>{req.movie_name.upper()}</a>"
        caption_text = (
            f"{movie_link}\n"
            f"<code>Внимание, фильм автоматически удалится через 15м.</code>"
        )
        
        msg = await bot.send_video(
            chat_id=req.user_id,
            video=req.file_id,
            caption=caption_text,
            parse_mode="HTML"
        )
        
        # Задача на удаление через 15 минут (900 секунд)
        async def delete_task(chat_id, message_id):
            await asyncio.sleep(900)
            try:
                await bot.delete_message(chat_id, message_id)
            except:
                pass
        
        asyncio.create_task(delete_task(req.user_id, msg.message_id))
        return {"status": "ok"}
    except Exception as e:
        print(f"Ошибка: {e}")
        raise HTTPException(status_code=500)

async def main():
    await init_db()
    # Сбрасываем вебхуки, чтобы не было конфликта
    await bot.delete_webhook(drop_pending_updates=True)
    
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
