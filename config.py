import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Не найден BOT_TOKEN в файле .env")

admin_id_str = os.getenv("ADMIN_ID")

if not admin_id_str:
    print("⚠️ ВНИМАНИЕ: не найден ADMIN_ID в .env")
    print("⚠️ Уведомления и /list работать не будут!")
    print("⚠️ Добавь в .env строку: ADMIN_ID=твой_id")
    ADMIN_ID = None
else:
    ADMIN_ID = int(admin_id_str)