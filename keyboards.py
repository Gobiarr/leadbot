from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="О нас")],
        [KeyboardButton(text="Оставить заявку")],
        [KeyboardButton(text="Связаться")],
    ],
    resize_keyboard=True,
)

# Варианты срока аренды
RENTAL_TERMS = ["До 6 месяцев", "6–12 месяцев", "Год и более"]

term_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=t)] for t in RENTAL_TERMS],
    resize_keyboard=True,
)


def get_contact_keyboard(admin_id: int) -> InlineKeyboardMarkup:
    """Кнопка связи с администратором."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✉️ Написать администратору",
                    url=f"tg://user?id={admin_id}",
                )
            ]
        ]
    )