from telegram.ext import ApplicationBuilder
from finance_bot import setup_handlers

def main():
    # Set a custom timeout while running the bot
    app = ApplicationBuilder().token("8036192196:AAGSxYxclHdmS1FvbO1baJyoTWcGirUR6rQ").build()

    setup_handlers(app)

    print("🤖 Bot is running...")
    app.run_polling(timeout=10)  # Set the timeout here (in seconds)

if __name__ == "__main__":
    main()

