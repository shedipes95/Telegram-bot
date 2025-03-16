import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # type: ignore
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import db  # your database module

# Load environment variables from .env file
load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

class TelegramBot:
    def __init__(self, token: str):
        self.application = ApplicationBuilder().token(token).build()
        
        # Initialize (or update) the database schema
        db.init_db()
        
        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("searchphotos", self.searchphotos_command))
        self.application.add_handler(CommandHandler("showphotos", self.showphotos_command))
        
        # Register message handlers (for text and photos)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.photo_handler))
        
        # Register callback query handler for inline menu selections
        self.application.add_handler(CallbackQueryHandler(self.menu_callback, pattern=r"^menu_"))
        self.application.add_handler(CallbackQueryHandler(self.choose_photo_callback, pattern=r"^choose_photo:"))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        welcome_text = (
            "Welcome! You can send me text messages or photos (with caption) and I'll save them.\n"
            "Use /search <keyword> to search all messages.\n"
            "Use /searchphotos <keyword> from:YYYY-MM-DD to:YYYY-MM-DD to search your photos.\n"
            "Use /showphotos to list all your saved photos.\n"
            "Or type /menu to see a clickable menu of options."
        )
        await update.message.reply_text(welcome_text)

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Inline keyboard with four buttons: Search, SearchPhotos, ShowPhotos, and Help.
        keyboard = [
            [
                InlineKeyboardButton("Search", callback_data="menu_search"),
                InlineKeyboardButton("SearchPhotos", callback_data="menu_searchphotos")
            ],
            [
                InlineKeyboardButton("ShowPhotos", callback_data="menu_showphotos"),
                InlineKeyboardButton("Help", callback_data="menu_help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Please choose an option from the menu:", reply_markup=reply_markup)

    async def menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()  # Acknowledge callback
        data = query.data  # Expected: "menu_search", "menu_searchphotos", "menu_showphotos", "menu_help"
        
        if data == "menu_search":
            text = "Usage: /search <keyword>\nExample: /search pancake"
            await query.edit_message_text(text=text)
        elif data == "menu_searchphotos":
            text = (
                "Usage: /searchphotos <keyword> from:YYYY-MM-DD to:YYYY-MM-DD\n"
                "All parameters are optional.\n\n"
                "Example: /searchphotos vacation from:2023-01-01 to:2023-01-31"
            )
            await query.edit_message_text(text=text)
        elif data == "menu_showphotos":
            # Call our handler to show photos
            await self.handle_show_photos(query, context)
        elif data == "menu_help":
            text = (
                "Available Commands:\n"
                "• /search - Search text messages and photo captions.\n"
                "• /searchphotos - Search photos with optional keyword and date range filters.\n"
                "• /showphotos - List all saved photos.\n"
                "• /menu - Show this menu.\n"
                "\nUse these commands by typing '/' or using the menu buttons."
            )
            await query.edit_message_text(text=text)
        else:
            await query.edit_message_text(text="Unknown menu option.")

    async def handle_show_photos(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = str(query.from_user.id)
        photos = db.list_photos(user_id)
        if photos:
            if len(photos) == 1:
                # If only one photo, send it directly.
                photo = photos[0]
                file_id = photo.get('image_file_id')
                caption = photo.get('caption', '')
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=file_id, caption=caption)
                await query.edit_message_text(text="Here is your photo.")
            else:
                # If multiple photos, list them with an inline keyboard for selection.
                keyboard = []
                for photo in photos:
                    caption_snippet = (photo['caption'][:20] + "...") if photo.get('caption') and len(photo['caption']) > 20 else (photo.get('caption') or "")
                    button_text = f"ID {photo['id']}: {caption_snippet}"
                    callback_data = f"choose_photo:{photo['id']}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text="Select a photo from your saved list:", reply_markup=reply_markup)
        else:
            await query.edit_message_text(text="No photos saved yet.")

    async def showphotos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Dedicated command to list all saved photos.
        If one photo exists, sends it directly.
        If multiple photos exist, presents an inline keyboard to choose one.
        """
        user_id = str(update.effective_user.id)
        photos = db.list_photos(user_id)
        if photos:
            if len(photos) == 1:
                photo = photos[0]
                file_id = photo.get('image_file_id')
                caption = photo.get('caption', '')
                await update.message.reply_photo(photo=file_id, caption=caption)
            else:
                keyboard = []
                for photo in photos:
                    caption_snippet = (photo['caption'][:20] + "...") if photo.get('caption') and len(photo['caption']) > 20 else (photo.get('caption') or "")
                    button_text = f"ID {photo['id']}: {caption_snippet}"
                    callback_data = f"choose_photo:{photo['id']}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Select a photo from your saved list:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("No photos saved yet.")

    async def choose_photo_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        try:
            _, photo_id_str = query.data.split(":")
            photo_id = int(photo_id_str)
        except (ValueError, IndexError):
            await query.edit_message_text("Invalid selection.")
            return

        user_id = str(query.from_user.id)
        photo_record = db.get_photo_by_id(photo_id, user_id)
        if photo_record:
            file_id = photo_record.get('image_file_id')
            caption = photo_record.get('caption', '')
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=file_id, caption=caption)
            await query.edit_message_text(text="Photo sent!")
        else:
            await query.edit_message_text(text="Photo not found.")

    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = str(update.effective_user.id)
        text = update.message.text
        db.insert_message(user_id, text=text)
        await update.message.reply_text("Your text message has been saved!")

    async def photo_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = str(update.effective_user.id)
        photo = update.message.photo[-1]  # highest resolution version
        file_id = photo.file_id
        caption = update.message.caption
        db.insert_message(user_id, image_file_id=file_id, caption=caption)
        await update.message.reply_text("Your photo has been saved!")

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("Usage: /search <keyword>")
            return
        keyword = " ".join(context.args)
        results = db.search_messages(keyword)
        if results:
            response_lines = [f"Found {len(results)} message(s):"]
            for row in results:
                line = f"[{row['timestamp']}]"
                if row.get('text'):
                    line += f" Text: {row['text']}"
                if row.get('caption'):
                    line += f" Caption: {row['caption']}"
                if row.get('image_file_id'):
                    line += f" (Image ID: {row['image_file_id']})"
                response_lines.append(line)
            response_text = "\n".join(response_lines)
        else:
            response_text = f"No messages found containing '{keyword}'."
        await update.message.reply_text(response_text)

    async def searchphotos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Usage: /searchphotos <keyword> from:YYYY-MM-DD to:YYYY-MM-DD
        All parameters are optional.
        - If no arguments are provided, displays usage instructions.
        - If exactly one photo is found, sends it.
        - If multiple photos are found, presents an inline keyboard to choose one.
        """
        user_id = str(update.effective_user.id)
        if not context.args:
            usage_text = (
                "Usage: /searchphotos <keyword> from:YYYY-MM-DD to:YYYY-MM-DD\n"
                "All parameters are optional.\n\n"
                "Example: /searchphotos vacation from:2023-01-01 to:2023-01-31"
            )
            await update.message.reply_text(usage_text)
            return

        keyword = ""
        start_date = None
        end_date = None
        for arg in context.args:
            if arg.lower().startswith("from:"):
                start_date = arg[5:]
            elif arg.lower().startswith("to:"):
                end_date = arg[3:]
            else:
                if keyword:
                    keyword += " " + arg
                else:
                    keyword = arg

        results = db.search_photos_filtered(user_id, keyword, start_date, end_date)
        if results:
            if len(results) == 1:
                photo = results[0]
                file_id = photo.get('image_file_id')
                caption = photo.get('caption', '')
                await update.message.reply_photo(photo=file_id, caption=caption)
            else:
                keyboard = []
                for photo in results:
                    caption_snippet = (photo['caption'][:20] + "...") if photo.get('caption') and len(photo['caption']) > 20 else (photo.get('caption') or "")
                    button_text = f"ID {photo['id']}: {caption_snippet}"
                    callback_data = f"choose_photo:{photo['id']}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Multiple photos found. Please choose one:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("No photos found with the given criteria.")

    def run(self):
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            # level=logging.INFO
        )
        self.application.run_polling()

def main():
    bot = TelegramBot(bot_token)
    bot.run()

if __name__ == "__main__":
    main()
