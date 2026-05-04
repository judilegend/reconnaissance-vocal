FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (e.g. for librosa and audio processing)
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install python packages
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt
# Copy the rest of the application
COPY app/ app/

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
