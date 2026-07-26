import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN
from database import db
from middlewares.forcesub import ForceSubMiddleware
from handlers.admin import router as admin_router
from handlers.user import router as user_router

logger = logging.getLogger(__name__)

async def setup_bot_commands(bot: Bot):
    """Registers default bot commands menu in Telegram."""
    commands = [
        BotCommand(command="start", description="🔄 Botni qayta ishga tushirish"),
        BotCommand(command="contact", description="✉️ Adminga murojaat qilish"),
        BotCommand(command="rate", description="⭐ Botni baholash"),
        BotCommand(command="help", description="❓ Yordam va ko'rsatmalar"),
        BotCommand(command="privacy", description="🔒 Maxfiylik siyosati"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands menu set successfully.")

async def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger.info("Starting Instagram & YouTube Downloader Bot...")

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing! Check your .env configuration.")
        sys.exit(1)

    # Initialize Database with WAL mode and locks
    await db.init_db()

    # Initialize Bot & Dispatcher with 300s timeout for large uploads
    session = AiohttpSession(timeout=300.0)
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Setup Bot Commands Menu
    await setup_bot_commands(bot)

    # Register Middlewares
    forcesub_middleware = ForceSubMiddleware()
    dp.message.outer_middleware(forcesub_middleware)
    dp.callback_query.outer_middleware(forcesub_middleware)

    # Register Routers
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # Delete Webhook & Start Polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started successfully and is polling for updates...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
