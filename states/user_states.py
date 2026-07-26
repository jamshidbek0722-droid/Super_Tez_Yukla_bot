from aiogram.fsm.state import State, StatesGroup

class ContactState(StatesGroup):
    waiting_for_message = State()

class RatingState(StatesGroup):
    waiting_for_comment = State()
