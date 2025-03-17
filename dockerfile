# Use a lightweight Python 3.10 image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Update package list and install netcat-openbsd (needed by wait-for-it.sh)
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the wait script into the container and make it executable
COPY scripts/wait-for-it.sh /app/wait-for-it.sh
RUN chmod +x /app/wait-for-it.sh

# Copy the rest of the application code into the container
COPY . /app/

# Use wait-for-it to wait for Postgres (using internal network) before starting the bot
CMD ["/app/wait-for-it.sh", "postgres:5432", "--", "python", "bot.py"]
