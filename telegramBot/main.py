import base64 as b64
import os
import shutil
import threading
import magic
import requests
from flask import Flask
from telegram.ext import Application, MessageHandler, filters, CommandHandler


async def reply(update, context):
    await update.message.reply_text(
        "Hello there! Please send your clock files here and I will export them to a zip file.")


async def start_decode(update, context):
    # Create output directory if it doesn't exist
    if not os.path.exists("output"):
        os.makedirs("output")

    file = await context.bot.get_file(update.message.document)
    url = "http://localhost:9200/api/clockface"  # Fixed double slash
    file_name = update.message.document.file_name

    allowed_extensions = ['clock2', 'clock', 'face']

    await file.download_to_drive(file_name)

    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_name)

    if file_type != "application/x-apple-binary-plist" and  file_type != "application/x-bplist":
        await update.message.reply_text(
            "Error: Invalid file content. Only 'Apple binary property list' files are accepted.")
        os.remove(file_name)
        return

    await update.message.reply_text("Received file. Processing now. Please wait...")  # Fixed typo

    try:
        files = {'file': open(file_name, 'rb')}
        r = requests.post(url, files=files)
        response = r.json()["files"]

        g = 0
        for i in response:
            base6 = i["content"]
            file_type = i["file_type"]
            extension = get_file_extension(file_type)

            # Decode the base64 content
            img_data = b64.b64decode(base6)

            # Write to file in binary mode
            with open(f"output/image{g}.{extension}", "wb") as f:
                f.write(img_data)
            g += 1

        # Make the zip file
        zip_file_name = file_name.replace('.zip', '') + ".zip"
        shutil.make_archive(zip_file_name.replace('.zip', ''), 'zip', "output")

        # Send the zip file
        with open(zip_file_name, "rb") as f:
            await context.bot.send_document(chat_id=update.message.chat_id, document=f)

        # Clean up
        os.remove(zip_file_name)
        for filename in os.listdir("output"):
            os.remove(os.path.join("output", filename))
        os.remove(file_name)

    except Exception as e:
        await update.message.reply_text(f"An error occurred during processing: {str(e)}")

    finally:
        # Close the file if it was opened
        if 'files' in locals() and hasattr(files['file'], 'close'):
            files['file'].close()


def get_file_extension(file_type_element):
    if file_type_element:
        if file_type_element == 'application/font-sfnt':
            return 'ttf'
        elif file_type_element == 'image/png':
            return 'png'
        elif file_type_element == 'video/quicktime':
            return 'mov'
        else:
            return file_type_element.split('/').pop()
    else:
        return 'png'  # Or handle the case where file_type_element is None


def main():
    # Use environment variable for token or load from config file
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "7694848459:AAFA9GFgJ2qHrAYfTA-ImA9aRksHsFIX_O8")
    application = Application.builder().token(token).concurrent_updates(True).read_timeout(30).write_timeout(30).build()

    application.add_handler(MessageHandler(filters.TEXT, reply))
    application.add_handler(CommandHandler("hello", reply))
    application.add_handler(MessageHandler(filters.ATTACHMENT, start_decode))

    print("Telegram Bot started!", flush=True)
    application.run_polling()


def run_flask():
    app = Flask(__name__)

    @app.route('/status')
    def status():
        return "Bot is running!", 200

    app.run(host='0.0.0.0', port=2221)


if __name__ == '__main__':
    # Ensure output directory exists
    if not os.path.exists("output"):
        os.makedirs("output")

    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # Make thread daemon so it exits when main thread exits
    flask_thread.start()

    # Start the Telegram bot
    main()