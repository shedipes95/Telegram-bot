import logging
import os
from dotenv import load_dotenv
from telegram import Update  
from telegram.ext import ( 
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import db  # Import our database module

# Load environment variables from .env file
load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

class TelegramBot:
    """
    A class-based Telegram bot that saves user messages in an SQLite database.
    It includes advanced search functionality using the /search command.
    """

    def __init__(self, token: str):
        self.token = token
        self.application = ApplicationBuilder().token(self.token).build()

        # Initialize the database (creates table if needed)
        db.init_db()

        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        # Register the search command handler
        self.application.add_handler(CommandHandler("search", self.search_command))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Hello! I’m your Virtual Assistant Bot.\n"
            "Send me any text message, and I’ll store it for you.\n"
            "Use /search <keyword> to find messages."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = str(update.effective_user.id)
        text = update.message.text

        # Save the message to the database
        db.insert_message(user_id, text)
        await update.message.reply_text("Your message has been saved in the database!")

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Check if a keyword was provided
        if not context.args:
            await update.message.reply_text("Please provide a keyword to search. Usage: /search <keyword>")
            return

        # Join the arguments into a keyword (supports multi-word queries)
        keyword = " ".join(context.args)
        results = db.search_messages(keyword)

        if results:
            response_lines = [f"Found {len(results)} message(s):"]
            for row in results:
                response_lines.append(f"[{row['timestamp']}] {row['text']}")
            response_text = "\n".join(response_lines)
        else:
            response_text = f"No messages found containing '{keyword}'."

        await update.message.reply_text(response_text)

    def run(self):
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            # Uncomment next line to enable INFO logging:
            # level=logging.INFO
        )
        self.application.run_polling()

def main():
    bot = TelegramBot(bot_token)
    bot.run()

if __name__ == "__main__":
    main()
