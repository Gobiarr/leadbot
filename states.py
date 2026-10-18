from aiogram.fsm.state import State, StatesGroup


class ApplicationForm(StatesGroup):
    budget = State()
    district = State()
    preferences = State()
    rental_term = State()