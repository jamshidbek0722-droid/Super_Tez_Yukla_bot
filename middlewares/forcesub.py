import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import TelegramObject, Message, CallbackQuery
from database import db
from utils.helpers import TEXT_FORCE_SUB
from keyboards.user import get_forcesub_keyboard

logger = logging.getLogger(__name__)

class ForceSubscribeMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Group chats bypass force-sub check completely
        if isinstance(event, Message):
            if event.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                return await handler(event, data)

            # Whitelist /start command so new users can execute /start or receive initial welcome
            if event.text and (event.text == "/start" or event.text.startswith("/start ")):
                return await handler(event, data)

        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # Whitelist Admins & Owner
        admins = await db.get_admins()
        if user.id in admins:
            return await handler(event, data)

        # Retrieve mandatory channels
        channels = await db.get_mandatory_channels()
        if not channels:
            return await handler(event, data)

        bot = data["bot"]
        unsubscribed_channels = []

        for ch in channels:
            try:
                cid = ch["channel_id"]
                # Convert string representation of int to int if numeric
                try:
                    cid = int(cid)
                except ValueError:
                    pass

                member = await bot.get_chat_member(chat_id=cid, user_id=user.id)
                if member.status in ["left", "kicked"]:
                    unsubscribed_channels.append(ch)
            except Exception as e:
                logger.warning(f"Could not check membership for channel {ch['channel_id']}: {e}")
                unsubscribed_channels.append(ch)

        if unsubscribed_channels:
            if isinstance(event, Message):
                await event.answer(
                    TEXT_FORCE_SUB,
                    reply_markup=get_forcesub_keyboard(channels),
                    parse_mode="HTML"
                )
                return  # Block handler execution

            elif isinstance(event, CallbackQuery):
                # Allow check_sub_status / check_forcesub callbacks through so handlers can verify
                if event.data in ["check_sub_status", "check_forcesub"]:
                    return await handler(event, data)
                else:
                    await event.answer(
                        "⚠️ Botdan foydalanish uchun rasmiy kanallarga a'zo bo'ling!",
                        show_alert=True
                    )
                    return  # Block handler execution

        return await handler(event, data)

# Alias for backward compatibility
ForceSubMiddleware = ForceSubscribeMiddleware
