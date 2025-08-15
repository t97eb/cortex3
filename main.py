import os
import logging
from telegram import Update, InputFile
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)
from dotenv import load_dotenv
from database import Session, User, MessageLog, PremiumCode
from file_handlers import extract_pdf_text, extract_docx_text, extract_image_text
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import pytz

# تحميل المتغيرات
load_dotenv()

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعدادات HuggingFace لإنشاء الصور
HF_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4"

# رسائل البوت
WELCOME_MESSAGE = """
🌟 *مرحباً بك في Cortex AI Bot* 🌟

🎁 لديك اليوم 10 طلبات مجانية (بما فيها إنشاء ملفين)
🔄 يتم تجديدها تلقائياً كل 24 ساعة

💎 للطلبات غير المحدودة:
👉 راسل @geenarl_bot
أو أرسل /premium

🚀 أرسل لي سؤالك الآن!
"""

PREMIUM_ACTIVATED_MESSAGE = """
✨ *مبروك!* ✨

🎉 تم تفعيل الباقة البريميوم بنجاح!

✅ طلبات غير محدودة
✅ إنشاء ملفات غير محدود
✅ إنشاء صور يوميًا: {} صورة
⏳ المدة: {} يوم

استمتع بتجربة Cortex AI الكاملة!
"""

# دوال مساعدة
def get_user(user_id: int) -> User:
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        user = User(
            user_id=user_id,
            remaining_requests=10,
            remaining_files=2,
            remaining_images=1,
            is_premium=False,
            last_request_date=datetime.now().strftime("%Y-%m-%d")
        )
        session.add(user)
        session.commit()
    session.close()
    return user

def update_user_limits(user_id: int, is_file=False, is_image=False) -> bool:
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        session.close()
        return False

    if user.is_premium:
        session.close()
        return True

    today = datetime.now().strftime("%Y-%m-%d")
    if user.last_request_date != today:
        user.remaining_requests = 10
        user.remaining_files = 2
        user.remaining_images = 1
        user.last_request_date = today
        session.commit()

    allowed = False
    if is_file and user.remaining_files > 0:
        user.remaining_files -= 1
        allowed = True
    elif is_image and user.remaining_images > 0:
        user.remaining_images -= 1
        allowed = True
    elif not is_file and not is_image and user.remaining_requests > 0:
        user.remaining_requests -= 1
        allowed = True

    session.commit()
    session.close()
    return allowed

def reset_daily_limits():
    session = Session()
    session.query(User).filter(User.is_premium == False).update({
        User.remaining_requests: 10,
        User.remaining_files: 2,
        User.remaining_images: 1,
        User.last_request_date: datetime.now().strftime("%Y-%m-%d")
    })
    session.commit()
    session.close()

# جدولة إعادة تعيين الطلبات اليومية
scheduler = BackgroundScheduler()
scheduler.add_job(reset_daily_limits, 'cron', hour=0, minute=0)
scheduler.start()

# دوال إنشاء الصور عبر HuggingFace
def generate_image(prompt: str) -> bytes:
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": prompt}
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    return None

# دوال الرد على المستخدمين
def start(update: Update, context: CallbackContext):
    user = get_user(update.effective_user.id)
    update.message.reply_text(WELCOME_MESSAGE, parse_mode='Markdown')

def premium_info(update: Update, context: CallbackContext):
    update.message.reply_text(
        "💎 *باقة Cortex AI البريميوم* 💎\n\n"
        "✅ طلبات غير محدودة\n"
        "✅ إنشاء ملفات غير محدود\n"
        "✅ إنشاء صور يوميًا: 12 صورة\n"
        "🚀 جميع ميزات الذكاء الاصطناعي\n\n"
        "للاستفسار أو الشراء:\n👉 @geenarl_bot",
        parse_mode='Markdown'
    )

def handle_premium_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    code = update.message.text.strip()
    session = Session()
    premium_code = session.query(PremiumCode).filter_by(code=code, is_used=False).first()
    if premium_code:
        premium_code.is_used = True
        premium_code.used_by = user_id
        premium_code.used_at = datetime.utcnow()
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.is_premium = True
            user.premium_expiry = datetime.now() + timedelta(days=premium_code.duration_days)
            user.remaining_images = 12
            session.commit()
            update.message.reply_text(
                PREMIUM_ACTIVATED_MESSAGE.format(12, premium_code.duration_days),
                parse_mode='Markdown'
            )
    else:
        update.message.reply_text("⚠️ الكود غير صالح أو منتهي الصلاحية")
    session.close()

def log_message(user_id: int, content: str, message_type: str):
    session = Session()
    log = MessageLog(user_id=user_id, content=content, message_type=message_type)
    session.add(log)
    session.commit()
    session.close()

def process_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    log_message(user_id, text, "text")

    # الردود القصيرة باللهجة العراقية
    if not update_user_limits(user_id):
        update.message.reply_text(
            "😅 انتهت الباقة اليومية، تقدر تواصل @geenarl_bot لتفعيل البريميوم"
        )
        return

    # مثال: الطقس والتاريخ واسم اليوم
    now = datetime.now(pytz.timezone("Asia/Baghdad"))
    date_info = f"📅 اليوم: {now.strftime('%A')} | التاريخ: {now.strftime('%d-%m-%Y')}"
    
    response = f"🗨️ {text} (رد قصير باللهجة العراقية)\n{date_info}"
    update.message.reply_text(response)

def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Error:", exc_info=context.error)

def main():
    updater = Updater(os.getenv('TELEGRAM_BOT_TOKEN'))
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('premium', premium_info))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, process_message))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
