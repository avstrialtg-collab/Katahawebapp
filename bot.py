import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
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
    if os.path.exists('index.html'):
        return FileResponse('index.html')
    return {"error": "index.html not found"}

@app.get("/movies")
async def get_movies():
    try:
        # Проверяем наличие файла БД перед подключением
        if not os.path.exists(DB_NAME):
            return {"error": f"Database file {DB_NAME} not found on server"}
            
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            # Используем названия колонок name и file_id из твоего скриншота
            async with db.execute("SELECT name, file_id FROM ratings") as cursor:
                movies = await cursor.fetchall()
                return [dict(row) for row in movies]
    except Exception as e:
        print(f"Database Error: {e}")
        return {"error": str(e)}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="KATAHA", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    text = (
        "Приветствую! Ты попал к нам в логово: <a href='https://t.me/der227'>KATAHA ВОЗВРАЩЕНИЕ</a>\n\n"
        "Нажми на кнопку ниже, чтобы запустить приложение."
    )
    try:
        if os.path.exists("banner.jpg"):
            await message.answer_photo(photo=FSInputFile("banner.jpg"), caption=text, parse_mode="HTML", reply_markup=markup)
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        await message.answer(text, parse_mode="HTML", reply_markup=markup)

@app.post("/select_movie")
async def select_movie(req: WatchRequest):
    try:
        movie_link = f"<b><a href='https://t.me/der227'>{req.movie_name.upper()}</a></b>"
        caption_text = f"{movie_link}\n<code>Внимание, фильм автоматически удалится через 15м.</code>"
        
        msg = await bot.send_video(
            chat_id=req.user_id,
            video=req.file_id,
            caption=caption_text,
            parse_mode="HTML"
        )
        
        async def auto_delete(chat_id, msg_id):
            await asyncio.sleep(900)
            try:
                await bot.delete_message(chat_id, msg_id)
            except:
                pass
        
        asyncio.create_task(auto_delete(req.user_id, msg.message_id))
        return {"status": "ok"}
    except Exception as e:
        print(f"Send Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
