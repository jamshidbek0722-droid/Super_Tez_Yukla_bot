from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from typing import List, Dict, Any, Union

def get_main_keyboard(is_admin: bool = False) -> Union[ReplyKeyboardMarkup, ReplyKeyboardRemove]:
    """
    UI/UX Cleanup:
    - Regular users get NO reply keyboard buttons (ReplyKeyboardRemove).
    - Admins ONLY receive a persistent 👑 Admin paneli Reply Keyboard.
    """
    if is_admin:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="👑 Admin paneli")]],
            resize_keyboard=True,
            persistent=True
        )
    return ReplyKeyboardRemove()

def get_start_inline_keyboard(bot_username: str = "Super_Tez_Yukla_Bot") -> InlineKeyboardMarkup:
    """Inline keyboard for /start welcome message (Add to Group button)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Guruhga qo'shish",
                    url=f"https://telegram.me/{bot_username}?startgroup=true"
                )
            ]
        ]
    )

def get_forcesub_keyboard(channels: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Builds inline keyboard for mandatory channel subscriptions."""
    buttons = []
    for ch in channels:
        name = ch.get("channel_name") or ch.get("title") or "Kanal"
        url = ch.get("invite_link", "")
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://t.me/{url.replace('@', '')}"
        buttons.append([InlineKeyboardButton(text=f"📢 {name}", url=url)])
    
    buttons.append([InlineKeyboardButton(text="✅ A'zo bo'ldim / Tekshirish", callback_data="check_sub_status")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_video_action_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard attached to EVERY downloaded video for audio extraction & video note conversion."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎵 Musiqasini olish", callback_data="extract_audio")],
            [InlineKeyboardButton(text="⭕️ Yumaloq video qilish", callback_data="convert_videonote")],
        ]
    )

def get_rating_keyboard() -> InlineKeyboardMarkup:
    """Returns 1-5 star rating inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 1", callback_data="rate_star:1"),
                InlineKeyboardButton(text="⭐ 2", callback_data="rate_star:2"),
                InlineKeyboardButton(text="⭐ 3", callback_data="rate_star:3"),
                InlineKeyboardButton(text="⭐ 4", callback_data="rate_star:4"),
                InlineKeyboardButton(text="⭐ 5", callback_data="rate_star:5"),
            ]
        ]
    )

def get_skip_comment_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard to skip rating comment."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Fikrsiz qoldirish", callback_data="rate_skip_comment")]
        ]
    )
