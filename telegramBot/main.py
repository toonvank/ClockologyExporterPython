import base64 as b64
import os
import shutil
import sys
import threading
import magic
import requests
from flask import Flask
from telegram.ext import Application, MessageHandler, filters, CommandHandler


async def reply(update, context):
    await update.message.reply_text("Hello there! Please send your clock files here and i will export them to a zip file.")

async def start_decode(update, context):
    try:
        file = await context.bot.get_file(update.message.document)
        url = "https://clockexporter.toonvank.online/api/clockface"
        file_name = update.message.document.file_name

        allowed_extensions = ['clock2', 'clock', 'face']
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            await update.message.reply_text(
                "Error: Invalid file type. Only '.clock2', '.clock', or '.face' files are accepted. Please try again.")
            return

        await file.download_to_drive(file_name)

        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_name)

        if file_type != "application/x-apple-binary-plist" and  file_type != "application/x-bplist":
            await update.message.reply_text(
                "Error: Invalid file content. Only 'Apple binary property list' files are accepted.")
            os.remove(file_name)
            return

        await update.message.reply_text("Recieved file. Processing now. Please wait...")

        files = {'file': open(file_name, 'rb')}
        await update.message.reply_text("Shutting down")

        raise Exception("Sorry, no numbers below zero")

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

        shutil.make_archive("output.zip".replace('.zip', ''), 'zip', "output")

        with open("output.zip", "rb") as f:
            await context.bot.send_document(chat_id=update.message.chat_id, document=f)
        f.close()

        os.remove("output.zip")
        shutil.rmtree("output")
        os.makedirs("output")
        os.remove(file_name)
    except Exception as e:
        sys.exit(1)


def get_file_extension(file_type_element):
    if file_type_element:
        if file_type_element == 'application/font-sfnt':
            extension = 'ttf'
        if file_type_element == 'image/png':
            extension = 'png'
        elif file_type_element == 'video/quicktime':
            extension = 'mov'
        else:
            extension = file_type_element.split('/').pop()
        return extension
    else:
        return 'png'  # Or handle the case where file_type_element is None


def main():
    token = "7694848459:AAFA9GFgJ2qHrAYfTA-ImA9aRksHsFIX_O8"
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
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Start the Telegram bot
    main()