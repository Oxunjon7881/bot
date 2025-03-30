from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from PIL import Image
import os
import nest_asyncio

nest_asyncio.apply()

TOKEN = "8063964842:AAH9BHZj1Cf1oR8ZbCR2NSglDud4kjaJV1E"
ADMIN_ID = 7341543176  # O'zgartiring

# Foydalanuvchilar uchun bepul slayd limiti
FREE_SLIDE_LIMIT = 5
user_slide_counts = {}
user_images = {}

# Rasmni qabul qilish va PDF ga o'girish funksiyasi
async def image_to_pdf(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]  # Eng yuqori sifatli rasmni olish
    file = await context.bot.get_file(photo.file_id)
    file_path = f"{file.file_id}.jpg"
    await file.download_to_drive(file_path)
    
    if user_id not in user_images:
        user_images[user_id] = []
    user_images[user_id].append(file_path)
    
   # await update.message.reply_text(f"✅ Jami qabul qilingan rasmlar: {len(user_images[user_id])}")
    
    if len(user_images[user_id]) == 1:
        await update.message.reply_text("📂 PDF fayl yaratish uchun fayl nomini kiriting:")

async def finalize_pdf(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    pdf_name = update.message.text + ".pdf"
    image_list = [Image.open(img).convert("RGB") for img in user_images.get(user_id, [])]
    
    if image_list:
        image_list[0].save(pdf_name, save_all=True, append_images=image_list[1:])
        await update.message.reply_document(document=open(pdf_name, "rb"), caption="✅ Hamma rasmlar bitta PDF ga saqlandi! Yangi yaratish uchun /start buyru'ini yuboring.")
        for img in user_images[user_id]:
            os.remove(img)
        os.remove(pdf_name)
        user_images[user_id] = []
    else:
        await update.message.reply_text("❌ Hech qanday rasm topilmadi.")

# Boshlang‘ich menyu
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📸 Rasmni PDF ga o‘girish", callback_data="convert_pdf")],
        [InlineKeyboardButton("📂 Hujjat yaratish", callback_data="create_doc")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Assalomu alaykum! Quyidagi funksiyalardan birini tanlang:", reply_markup=reply_markup)

# Admin panel
async def admin_panel(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Sizda ushbu bo‘limga kirish huquqi yo‘q!")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton("💰 Foydalanuvchi hisoblari", callback_data="accounts")],
        [InlineKeyboardButton("🔧 Xizmatlarni boshqarish", callback_data="services")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👑 Admin Paneliga xush kelibsiz!", reply_markup=reply_markup)

# Foydalanuvchining slayd yaratish limitini tekshirish
async def check_slide_limit(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_slide_counts[user_id] = user_slide_counts.get(user_id, 0) + 1
    
    if user_slide_counts[user_id] > FREE_SLIDE_LIMIT:
        await update.message.reply_text("❌ Sizning bepul slayd yaratish limitingiz tugadi! Hisobingizni to‘ldirish uchun admin bilan bog‘laning.")
        return
    
    await update.message.reply_text(f"✅ Siz {FREE_SLIDE_LIMIT - user_slide_counts[user_id]} ta bepul slayd yaratishingiz mumkin.")

# Tugmalar uchun handler
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "convert_pdf":
        await query.message.reply_text("📤 Iltimos, PDF ga o‘girish uchun rasm yuboring!")
    elif query.data == "create_doc":
        keyboard = [
            [InlineKeyboardButton("📝 Slayd yaratish", callback_data="create_slide")],
            [InlineKeyboardButton("📑 Mustaqil ish yaratish", callback_data="create_independent_work")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("📂 Hujjat turini tanlang:", reply_markup=reply_markup)

# Botni ishga tushirish
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))  # Faqat /admin orqali admin panelga kirish
    app.add_handler(MessageHandler(filters.PHOTO, image_to_pdf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, finalize_pdf))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
