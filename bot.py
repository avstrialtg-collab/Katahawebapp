import asyncio
import time
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, FSInputFile
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import os

# --- НАСТРОЙКИ ---
TOKEN = "8389025017:AAHoEJhU2saMWfP50pv_d6kbjuiv_GKIliE"
DB_NAME = "bot_data.db"
# Используй свой URL от Render здесь
WEB_APP_URL = "https://katahawebapp.onrender.com" 

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

# Главная страница сайта (исправляет 404)
@app.get("/")
async def read_index():
    return FileResponse('index.html')

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Убрали стикеры, оставили только кнопку KATAHA
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="KATAHA", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])

    # Текст с кликабельной ссылкой
    text = (
        "Приветствую! Ты попал к нам в логово: <a href='https://t.me/der227'>KATAHA ВОЗВРАЩЕНИЕ</a>\n\n"
        "Нажми на кнопку ниже, чтобы запустить приложение."
    )
    
    try:
        # Отправка с баннером
        banner = FSInputFile("banner.jpg")
        await message.answer_photo(photo=banner, caption=text, parse_mode="HTML", reply_markup=markup)
    except Exception:
        # Если баннер не найден, шлем просто текст
        await message.answer(text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)

@app.get("/movies")
async def get_movies():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        # Запрос к таблице (проверь название таблицы в БД, на скринах была 'ratings')
        async with db.execute("SELECT movie as name, file_id, sum_rating, count FROM ratings") as cursor:
            movies = await cursor.fetchall()
            return [dict(row) for row in movies]

@app.post("/select_movie")
async def select_movie(req: WatchRequest):
    try:
        # Формат сообщения как в bot1 (Название со ссылкой и моно-текст)
        movie_link = f"<b><a href='https://t.me/der227'>{req.movie_name.upper()}</a></b>"
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
        
        # Удаление через 15 минут (900 секунд)
        async def auto_delete(chat_id, msg_id):
            await asyncio.sleep(900)
            try:
                await bot.delete_message(chat_id, msg_id)
            except:
                pass
        
        asyncio.create_task(auto_delete(req.user_id, msg.message_id))
        return {"status": "ok"}
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        raise HTTPException(status_code=500)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
