import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from database import init_db, save_application, get_applications

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Не найден BOT_TOKEN в файле .env")

ADMIN_ID = os.getenv("ADMIN_ID")

if not ADMIN_ID:
    print("⚠️ ВНИМАНИЕ: не найден ADMIN_ID в .env — уведомления и /list работать не будут!")
    print("⚠️ Добавь в .env строку: ADMIN_ID=твой_id")
else:
    ADMIN_ID = int(ADMIN_ID)


# Создаём диспетчер с хранилищем состояний
dp = Dispatcher(storage=MemoryStorage())


# Состояния анкеты
class ApplicationForm(StatesGroup):
    budget = State()
    district = State()
    preferences = State()
    rental_term = State()


# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="О нас")],
        [KeyboardButton(text="Оставить заявку")],
        [KeyboardButton(text="Связаться")],
    ],
    resize_keyboard=True,
)

# Варианты срока аренды (кнопки)
RENTAL_TERMS = ["До 6 месяцев", "6–12 месяцев", "Год и более"]

term_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=t)] for t in RENTAL_TERMS],
    resize_keyboard=True,
)


# Команда /start
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Привет! Я LeadBot.\n"
        "Помогу оставить заявку на аренду жилья.\n"
        "Выбери действие:",
        reply_markup=main_menu,
    )


# Кнопка «О нас»
@dp.message(lambda message: message.text == "О нас")
async def about_handler(message: Message):
    await message.answer(
        "Мы помогаем подобрать жильё для аренды."
    )


# Начинаем анкету
@dp.message(lambda message: message.text == "Оставить заявку")
async def application_handler(message: Message, state: FSMContext):
    await state.set_state(ApplicationForm.budget)

    await message.answer(
        "Шаг 1 из 4.\n"
        "Какой у тебя бюджет на аренду в месяц?\n"
        "Напиши цифрами, например: 50000",
        reply_markup=ReplyKeyboardRemove(),
    )


# Команда для отмены анкеты
@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Заполнение анкеты отменено.",
        reply_markup=main_menu,
    )


# Команда /list — только для админа
@dp.message(Command("list"))
async def list_handler(message: Message):
    if not ADMIN_ID or message.from_user.id != ADMIN_ID:
        await message.answer("У тебя нет доступа к этой команде.")
        return

    applications = get_applications(limit=10)

    if not applications:
        await message.answer("Заявок пока нет.")
        return

    lines = ["📋 Последние заявки:\n"]
    for app in applications:
        app_id, user_id, budget, district, preferences, rental_term, created_at = app
        lines.append(
            f"📝 Заявка #{app_id} · {created_at}\n"
            f"👤 ID пользователя: {user_id}\n"
            f"💰 Бюджет: {budget}\n"
            f"📍 Район: {district}\n"
            f"⭐ Предпочтения: {preferences}\n"
            f"📅 Срок: {rental_term}\n"
        )

    await message.answer("\n".join(lines))


# Получаем бюджет (только цифры)
@dp.message(ApplicationForm.budget)
async def process_budget(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, напиши бюджет цифрами.")
        return

    budget_text = message.text.strip()

    if not budget_text.replace(" ", "").isdigit():
        await message.answer(
            "Бюджет нужно написать цифрами, например: 50000"
        )
        return

    await state.update_data(budget=budget_text)

    await state.set_state(ApplicationForm.district)

    await message.answer(
        "Шаг 2 из 4.\n"
        "В каком районе хочешь снять жильё?"
    )


# Получаем район
@dp.message(ApplicationForm.district)
async def process_district(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, напиши район текстом.")
        return

    await state.update_data(district=message.text)

    await state.set_state(ApplicationForm.preferences)

    await message.answer(
        "Шаг 3 из 4.\n"
        "Какое жильё тебе нужно? "
        "Опиши предпочтения: количество комнат, мебель и другое."
    )


# Получаем предпочтения
@dp.message(ApplicationForm.preferences)
async def process_preferences(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, напиши предпочтения текстом.")
        return

    await state.update_data(preferences=message.text)

    await state.set_state(ApplicationForm.rental_term)

    await message.answer(
        "Шаг 4 из 4.\n"
        "На какой срок планируешь арендовать жильё? "
        "Выбери вариант кнопкой:",
        reply_markup=term_keyboard,
    )


# Получаем срок (только кнопки) и завершаем анкету
@dp.message(ApplicationForm.rental_term)
async def process_rental_term(message: Message, state: FSMContext):
    if not message.text or message.text not in RENTAL_TERMS:
        await message.answer(
            "Выбери срок аренды одной из кнопок 👇",
            reply_markup=term_keyboard,
        )
        return

    await state.update_data(rental_term=message.text)
    data = await state.get_data()

    # Сохраняем заявку в SQLite
    save_application(
        user_id=message.from_user.id,
        budget=data["budget"],
        district=data["district"],
        preferences=data["preferences"],
        rental_term=data["rental_term"],
    )

    # Отправляем уведомление админу
    if ADMIN_ID:
        notification_text = (
            "🔔 Новая заявка!\n\n"
            f"👤 Пользователь: {message.from_user.full_name} "
            f"(ID: {message.from_user.id})\n"
            f"💰 Бюджет: {data['budget']}\n"
            f"📍 Район: {data['district']}\n"
            f"⭐ Предпочтения: {data['preferences']}\n"
            f"📅 Срок аренды: {data['rental_term']}"
        )

        try:
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=notification_text,
            )
            print("✅ Уведомление админу отправлено")
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление: {e}")
    else:
        print("⚠️ ADMIN_ID не задан — уведомление пропущено")

    await message.answer(
        "Заявка заполнена!\n\n"
        f"Бюджет: {data['budget']}\n"
        f"Район: {data['district']}\n"
        f"Предпочтения: {data['preferences']}\n"
        f"Срок аренды: {data['rental_term']}",
        reply_markup=main_menu,
    )

    await state.clear()


# Кнопка «Связаться»
@dp.message(lambda message: message.text == "Связаться")
async def contact_handler(message: Message):
    if ADMIN_ID:
        contact_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✉️ Написать администратору",
                        url=f"tg://user?id={ADMIN_ID}",
                    )
                ]
            ]
        )
        await message.answer(
            "Нажми кнопку ниже, чтобы написать администратору:",
            reply_markup=contact_keyboard,
        )
    else:
        await message.answer(
            "Свяжитесь с администратором: @YOUR_USERNAME"
        )


async def main():
    init_db()

    bot = Bot(token=TOKEN)
    print("LeadBot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())