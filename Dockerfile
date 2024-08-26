# Use a more minimal base image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for uploaded files
RUN mkdir /app/uploaded_files

# Copy application files
COPY ./app /app

# Expose the port that the Dash app will run on
EXPOSE 8080

# Command to run the application with Waitress
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "app:server"]
