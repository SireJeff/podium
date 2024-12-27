# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to optimize Python's behavior in Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app/

# Run database migrations before starting the bot
RUN python update_db.py

# Define the entry point to start the bot
CMD ["python", "app.py"]
