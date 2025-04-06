from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from yt_dlp import YoutubeDL
import os
import logging
Import block is un-sorted or un-formatted

from keep_alive import keep_alive

keep_alive()




TOKEN = '6767447234:AAHODYTwpqlNl0mbeGLK9qAtgKVHfHC0e40'
DOWNLOAD_FOLDER = 'downloads'  # Specify your download folder

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[
        InlineKeyboardButton("Download Video", callback_data='download_video'),
        InlineKeyboardButton("Convert Video to Audio",
                             callback_data='convert_video_to_audio'),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Choose an option:',
                                    reply_markup=reply_markup)


async def button_handler(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    if query.data == 'download_video':
        await query.message.reply_text(
            'Please send me the YouTube link to download the video.')
        context.user_data['action'] = 'download_video'  # Store action
    elif query.data == 'convert_video_to_audio':
        await query.message.reply_text(
            'Please send me the YouTube link to convert to audio.')
        context.user_data['action'] = 'convert_video_to_audio'  # Store action


async def handle_message(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
    user_action = context.user_data.get('action')

    if user_action == 'download_video':
        await download_video(update, context)
    elif user_action == 'convert_video_to_audio':
        await convert_video_to_audio(update, context)
    else:
        await update.message.reply_text(
            'Please select an option using the buttons.')


async def download_video(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    youtube_url = update.message.text  # Get the YouTube link from the message

    if 'youtube.com' in youtube_url or 'youtu.be' in youtube_url:
        try:
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'cookies': 'cookiebro-cookies'
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                video_file_path = ydl.prepare_filename(info_dict)

            await context.bot.send_video(chat_id=chat_id,
                                         video=open(video_file_path, 'rb'))
            os.remove(video_file_path)

        except Exception as e:
            logging.error(f"Error processing YouTube link: {e}")
            await update.message.reply_text(
                "Error processing YouTube link. Please try again.")
    else:
        await update.message.reply_text("Please provide a valid YouTube link.")


async def convert_video_to_audio(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    youtube_url = update.message.text  # Get the YouTube link from the message

    if 'youtube.com' in youtube_url or 'youtu.be' in youtube_url:
        try:
            ydl_opts = {
                'format':
                'bestaudio/best',
                'outtmpl':
                os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                mp3_file_path = ydl.prepare_filename(info_dict).replace(
                    '.webm', '.mp3').replace('.m4a', '.mp3')

            await context.bot.send_audio(chat_id=chat_id,
                                         audio=open(mp3_file_path, 'rb'))
            os.remove(mp3_file_path)

        except Exception as e:
            logging.error(f"Error processing YouTube link: {e}")
            await update.message.reply_text(
                "Error processing YouTube link. Please try again.")
    else:
        await update.message.reply_text("Please provide a valid YouTube link.")


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler(
        "start", start))  # Handler for /start command
    application.add_handler(
        CallbackQueryHandler(button_handler))  # Handler for button presses
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND,
                       handle_message))  # Handle messages

    application.run_polling()


if __name__ == '__main__':
    main()


