import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from app.graph import process_message

load_dotenv()
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk command /start."""
    welcome_text = (
        "Halo! Selamat datang di Layanan Informasi AI Desa Wisata Lembah Asri.\n\n"
        "Saya dapat membantu Anda dengan:\n"
        "• Informasi paket wisata & fasilitas\n"
        "• Cek perkiraan cuaca terkini di Lembah Asri\n"
        "• Kalkulasi estimasi harga kunjungan\n"
        "• Reservasi / booking kunjungan\n\n"
        "Silakan ketik pertanyaan Anda atau gunakan /reset untuk memulai percakapan baru."
    )
    if update.effective_message:
        await update.effective_message.reply_text(welcome_text)


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk command /reset (mereset sesi/thread percakapan)."""
    chat_id = update.effective_chat.id if update.effective_chat else 0
    # Logika reset context / memory dapat dikustomisasi lebih lanjut pada graph state
    if update.effective_message:
        await update.effective_message.reply_text(
            f"Sesi percakapan Anda (ID: {chat_id}) telah direset. Ada yang bisa saya bantu kembali?"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk pesan teks masuk, meneruskannya ke LangGraph."""
    if not update.effective_message or not update.effective_message.text:
        return

    chat_id = str(update.effective_chat.id if update.effective_chat else "default")
    user_input = update.effective_message.text

    try:
        # Mengirim respon memproses
        response_text = await process_message(user_input=user_input, thread_id=chat_id)
        await update.effective_message.reply_text(response_text)
    except Exception as e:
        logger.error(f"Error memproses pesan untuk thread {chat_id}: {e}", exc_info=True)
        await update.effective_message.reply_text(
            "Mohon maaf, terjadi kendala saat memproses pertanyaan Anda. Silakan coba beberapa saat lagi."
        )


def create_bot_app():
    """Factory function untuk inisialisasi aplikasi python-telegram-bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        raise ValueError("TELEGRAM_BOT_TOKEN belum diset di file .env")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


async def run_bot() -> None:
    """Runner fungsi untuk menjalankan bot polling secara asinkron."""
    bot_app = create_bot_app()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    logger.info("Bot Telegram sedang aktif mendengarkan pesan...")
