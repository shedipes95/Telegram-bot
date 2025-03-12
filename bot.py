import logging
import json
import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()  

# Get the bot token from the environment variable
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

from telegram import Update # type: ignore
from telegram.ext import ( # type: ignore
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

class TelegramBot:
    """
    A class-based Telegram bot that saves user messages in a JSON file.
    Designed for easy expansion with new features.
    """

    DATA_FILE = "user_data.json"

    def __init__(self, token: str):
        """
        Initialize the bot with a given token and set up the application.
        """
        self.token = token
        self.application = ApplicationBuilder().token(self.token).build()

        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    @staticmethod
    def load_data() -> Dict[str, List[str]]:
        """
        Load user data from DATA_FILE if it exists, otherwise return an empty dict.
        """
        if os.path.exists(TelegramBot.DATA_FILE):
            with open(TelegramBot.DATA_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        return {}

    @staticmethod
    def save_data(data: Dict[str, List[str]]) -> None:
        """
        Save the provided data dictionary into DATA_FILE in JSON format.
        """
        with open(TelegramBot.DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

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
        Handler for incoming text messages. Saves the user's message in a JSON file.
        """
        user_id = str(update.effective_user.id)
        text = update.message.text

        # Load existing data
        data = self.load_data()

        # Append the new message to this user's list
        data.setdefault(user_id, []).append(text)

        # Save updated data
        self.save_data(data)

        # Reply to confirm
        await update.message.reply_text("Your message has been saved!")

    def run(self):
        """
        Start the bot using polling. For production, you might switch to webhooks.
        """
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            # level=logging.INFO
        )
        self.application.run_polling()


def main():
    # Replace with your actual token
    # bot_token = "7293396230:AAFLSLHeg6t87mTYSFdNejtTOlKdCYRJQuU"
    bot = TelegramBot(bot_token)
    bot.run()

if __name__ == "__main__":
    main()
