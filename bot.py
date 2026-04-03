import asyncio
import aiosqlite
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, FSInputFile
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# --- НАСТРОЙКИ ---
TOKEN = "8389025017:AAHoEJhU2saMWfP50pv_d6kbjuiv_GKIliE"
DB_NAME = "bot_data.db"
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

@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.get("/movies")
async def get_movies():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            # ИСПРАВЛЕНО: берем 'movie' (из твоей БД) и называем его 'name' для фронтенда
            async with db.execute("SELECT movie as name, file_id FROM ratings") as cursor:
                movies = await cursor.fetchall()
                result = [dict(row) for row in movies]
                print(f"Отправлено фильмов: {len(result)}")
                return result
    except Exception as e:
        print(f"Database Error: {e}")
        return {"error": str(e)}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="KATAHA", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    text = "Приветствую! Нажми на кнопку ниже, чтобы запустить приложение."
    try:
        await message.answer_photo(photo=FSInputFile("banner.jpg"), caption=text, reply_markup=markup)
    except:
        await message.answer(text, reply_markup=markup)

@app.post("/select_movie")
async def select_movie(req: WatchRequest):
    try:
        msg = await bot.send_video(chat_id=req.user_id, video=req.file_id, caption=f"<b>{req.movie_name}</b>", parse_mode="HTML")
        return {"status": "ok"}
    except Exception as e:
        print(f"Send Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def main():
    # Удаляем вебхук и старые обновления, чтобы не было конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
