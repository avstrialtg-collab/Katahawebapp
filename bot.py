# Добавь в импорты
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if await is_banned(message.from_user.id): return
    
    # Регистрация в БД (твой код)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (id, full_name, join_date) VALUES (?, ?, ?)", 
                         (message.from_user.id, message.from_user.full_name, int(time.time())))
        await db.commit()

    # Ссылка на твой развернутый index.html на GitHub Pages
    WEB_APP_URL = "https://avstrialtg-collab.github.io/Katahawebapp/"

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 ОТКРЫТЬ КАТАЛОГ", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])

    text = (
        "Приветствую! Ты попал к нам в логово: <b>KATAHA ВОЗВРАЩЕНИЕ</b>\n\n"
        "Пожалуйста, нажми на кнопку ниже, чтобы запустить приложение и выбрать фильм."
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=markup)