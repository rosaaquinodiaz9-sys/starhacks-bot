from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os

TOKEN = os.environ.get("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Ver Productos", callback_data="ver_productos")]
    ]
    await update.message.reply_text("¡Bienvenido a Starhacks Store! 👋", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "ver_productos":
        keyboard = [
            [InlineKeyboardButton("📱 Cuban Mods Mobile", callback_data="mobile")],
            [InlineKeyboardButton("💻 Cuban Mods PC", callback_data="pc")],
        ]
        await query.edit_message_text("Elige un producto:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "mobile":
        keyboard = [
            [InlineKeyboardButton("🛒 1 Día - $0.99", callback_data="m1")],
            [InlineKeyboardButton("🛒 7 Días - $1.98", callback_data="m7")],
            [InlineKeyboardButton("🛒 15 Días - $3.96", callback_data="m15")],
            [InlineKeyboardButton("🛒 30 Días - $7.92", callback_data="m30")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="ver_productos")]
        ]
        await query.edit_message_text("📦 Cuban Mods Mobile:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "pc":
        keyboard = [
            [InlineKeyboardButton("🛒 1 Día - $0.99", callback_data="p1")],
            [InlineKeyboardButton("🛒 7 Días - $4.95", callback_data="p7")],
            [InlineKeyboardButton("🛒 30 Días - $8.91", callback_data="p30")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="ver_productos")]
        ]
        await query.edit_message_text("📦 Cuban Mods PC:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["m1","m7","m15","m30","p1","p7","p30"]:
        await query.edit_message_text("✅ Plan seleccionado!\nContacta al admin para pagar.")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
print("✅ Bot corriendo...")
app.run_polling()
