import asyncio
import aiosqlite
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot

# Используем данные из твоего bot.py
TOKEN = "8318172496:AAEy7qjJa-lQZW50Js6CKjLTieo2u8SrmPw"
DB_NAME = "bot_data.db"

app = FastAPI()
bot = Bot(token=TOKEN)

# Настройка CORS для работы WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/movies")
async def get_movies():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT m.name, m.file_id, r.sum_rating, r.count FROM movies m LEFT JOIN ratings r ON m.name = r.movie") as cursor:
            movies = await cursor.fetchall()
            return [dict(row) for row in movies]

class WatchRequest(BaseModel):
    user_id: int
    movie_name: str
    file_id: str

@app.post("/select_movie")
async def select_movie(req: WatchRequest):
    try:
        # Логика отправки фильма из твоего бота
        caption = f"<b><a href='https://t.me/der227'>{req.movie_name.upper()}</a></b>\n<code>Авто-удаление через 15м.</code>"
        msg = await bot.send_video(req.user_id, video=req.file_id, caption=caption, parse_mode="HTML")
        
        # Фоновая задача на удаление
        async def delete_later(chat_id, msg_id):
            await asyncio.sleep(900)
            try: await bot.delete_message(chat_id, msg_id)
            except: pass
        
        asyncio.create_task(delete_later(req.user_id, msg.message_id))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)