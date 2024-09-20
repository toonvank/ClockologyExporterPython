import requests
from django.utils.baseconv import base64
from telegram.ext import Application, MessageHandler, filters, CommandHandler
import base64 as b64
import shutil


async def reply(update, context):
    await update.message.reply_text("Hello there!")

async def start_decode(update, context):
    file = await context.bot.get_file(update.message.document)
    url = "https://clockexporter.toonvank.online/api/clockface"
    await file.download_to_drive('test.clock2')

    files = {'file': open('test.clock2', 'rb')}

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

    # Send the zip file back to the user
    with open("output.zip", "rb") as f:
        await context.bot.send_document(chat_id=update.message.chat_id, document=f)

    # Confirmation message
    await update.message.reply_text("Success.")


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


if __name__ == '__main__':
    main()