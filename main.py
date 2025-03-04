import sys
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# إعداد التسجيل للأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
from yt_dlp import YoutubeDL
import os
import logging
import subprocess
import tempfile

TOKEN = '6767447234:AAHODYTwpqlNl0mbeGLK9qAtgKVHfHC0e40'
DOWNLOAD_FOLDER = 'downloads'  # مجلد التنزيلات

# إنشاء مجلد التنزيلات إذا لم يكن موجودًا
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# التحقق من وجود ffmpeg
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("ffmpeg غير مثبت في النظام. الرجاء تثبيته لتتمكن من تنزيل وتحويل الفيديوهات.")
        return False

HAS_FFMPEG = check_ffmpeg()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Download Video", callback_data='download_video'),
            InlineKeyboardButton("Convert Video to Audio", callback_data='convert_video_to_audio'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Choose an option:', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    if query.data == 'download_video':
        await query.message.reply_text('Please send me the YouTube link to download the video.')
        context.user_data['action'] = 'download_video'  # Store action
    elif query.data == 'convert_video_to_audio':
        await query.message.reply_text('Please send me the YouTube link to convert to audio.')
        context.user_data['action'] = 'convert_video_to_audio'  # Store action

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_action = context.user_data.get('action')

    if user_action == 'download_video':
        await download_video(update, context)
    elif user_action == 'convert_video_to_audio':
        await convert_video_to_audio(update, context)
    else:
        await update.message.reply_text('Please select an option using the buttons.')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    youtube_url = update.message.text  # الحصول على رابط يوتيوب من الرسالة

    if not HAS_FFMPEG:
        await update.message.reply_text("ffmpeg غير مثبت. لا يمكن تنزيل الفيديو.")
        return

    if 'youtube.com' in youtube_url or 'youtu.be' in youtube_url:
        status_message = await update.message.reply_text("جاري تنزيل الفيديو... يرجى الانتظار")
        try:
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                video_file_path = ydl.prepare_filename(info_dict)
                
                # التحقق من حجم الملف (حد تليجرام هو 50 ميجابايت)
                file_size = os.path.getsize(video_file_path) / (1024 * 1024)  # بالميجابايت
                
                if file_size > 50:
                    await status_message.edit_text(f"حجم الفيديو كبير جدًا ({file_size:.1f} MB). تليجرام يدعم حتى 50 MB.")
                    os.remove(video_file_path)
                    return

            await status_message.edit_text("اكتمل التنزيل، جاري الإرسال...")
            with open(video_file_path, 'rb') as video_file:
                await context.bot.send_video(chat_id=chat_id, video=video_file)
                
            await status_message.delete()
            os.remove(video_file_path)

        except Exception as e:
            logger.error(f"خطأ في معالجة رابط YouTube: {e}")
            await status_message.edit_text("حدث خطأ أثناء معالجة رابط YouTube. يرجى المحاولة مرة أخرى.")
    else:
        await update.message.reply_text("يرجى تقديم رابط YouTube صالح.")

async def convert_video_to_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    youtube_url = update.message.text  # الحصول على رابط يوتيوب من الرسالة

    if not HAS_FFMPEG:
        await update.message.reply_text("ffmpeg غير مثبت. لا يمكن تحويل الفيديو إلى صوت.")
        return

    if 'youtube.com' in youtube_url or 'youtu.be' in youtube_url:
        status_message = await update.message.reply_text("جاري تحويل الفيديو إلى صوت... يرجى الانتظار")
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                title = info_dict.get('title', 'audio')
                mp3_file_path = os.path.join(DOWNLOAD_FOLDER, f"{title}.mp3")
                
                # التحقق من وجود الملف بالاسم المتوقع
                if not os.path.exists(mp3_file_path):
                    # البحث عن ملف mp3 في مجلد التنزيلات
                    for file in os.listdir(DOWNLOAD_FOLDER):
                        if file.endswith('.mp3'):
                            mp3_file_path = os.path.join(DOWNLOAD_FOLDER, file)
                            break

                # التحقق من حجم الملف (حد تليجرام هو 50 ميجابايت)
                file_size = os.path.getsize(mp3_file_path) / (1024 * 1024)  # بالميجابايت
                if file_size > 50:
                    await status_message.edit_text(f"حجم الملف الصوتي كبير جدًا ({file_size:.1f} MB). تليجرام يدعم حتى 50 MB.")
                    os.remove(mp3_file_path)
                    return

            await status_message.edit_text("اكتمل التحويل، جاري الإرسال...")
            with open(mp3_file_path, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=chat_id, 
                    audio=audio_file,
                    title=title,
                    performer="YouTube"
                )
                
            await status_message.delete()
            os.remove(mp3_file_path)

        except Exception as e:
            logger.error(f"خطأ في معالجة رابط YouTube: {e}")
            await status_message.edit_text("حدث خطأ أثناء تحويل الفيديو إلى صوت. يرجى المحاولة مرة أخرى.")
    else:
        await update.message.reply_text("يرجى تقديم رابط YouTube صالح.")

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))  # Handler for /start command
    application.add_handler(CallbackQueryHandler(button_handler))  # Handler for button presses
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Handle messages

    application.run_polling()

if __name__ == '__main__':
    main()