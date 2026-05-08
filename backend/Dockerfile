FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances système (nécessaires pour librosa et le traitement audio)
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copie du fichier de dépendances corrigé
COPY requirements.txt .

# Mise à jour de pip ET installation des paquets Python
# (Ajouter la mise à jour de pip garantit le bon support de l'option --find-links pour PyTorch CPU)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copie du reste de l'application
COPY app/ app/

# Exposition du port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]