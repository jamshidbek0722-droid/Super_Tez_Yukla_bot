from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union
from config import is_owner
from database import db

class IsAdmin(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        user = event.from_user
        if not user:
            return False
        if is_owner(user.id):
            return True
        admins = await db.get_admins()
        return user.id in admins

class IsOwner(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        user = event.from_user
        return bool(user and is_owner(user.id))
