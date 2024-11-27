# Use Python base image
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Install necessary packages
RUN apt-get update && apt-get install -y libmagic1 file

# Copy all files from the project directory to the container
COPY . /app/

# Install dependencies for both the Flask app and the Telegram bot
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r /app/telegramBot/requirements.txt

# Command to run Flask app and Telegram bot
CMD gunicorn -w 4 -b 0.0.0.0:9200 app:app & python3 /app/telegramBot/main.py

