import logging
import os
from dotenv import load_dotenv
from telegram import Update  # type: ignore
from telegram.ext import ( # type: ignore
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Load environment variables from .env file
load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

# Import our database module (using SQLite)
import db

class TelegramBot:
    """
    A class-based Telegram bot that saves user messages in an SQLite database.
    Designed for easy expansion with new features.
    """

    def __init__(self, token: str):
        """
        Initialize the bot with a given token and set up the application.
        Also, initialize the database.
        """
        self.token = token
        self.application = ApplicationBuilder().token(self.token).build()

        # Initialize the database (creates the messages table if it doesn't exist)
        db.init_db()

        # Register command and message handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handler for the /start command. Greets the user.
        """
        await update.message.reply_text(
            "Hello! I’m your Virtual Assistant Bot.\n"
            "Send me any text message, and I’ll store it for you."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handler for incoming text messages.
        Saves the user's message in the SQLite database.
        """
        user_id = str(update.effective_user.id)
        text = update.message.text

        # Save the message to the database
        db.insert_message(user_id, text)

        # Confirm the message was saved
        await update.message.reply_text("Your message has been saved in the database!")

    def run(self):
        """
        Start the bot using polling. For production, consider switching to webhooks.
        """
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            # level=logging.INFO  # Uncomment to enable INFO level logging
        )
        self.application.run_polling()


def main():
    bot = TelegramBot(bot_token)
    bot.run()


if __name__ == "__main__":
    main()
