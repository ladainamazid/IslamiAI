# Dockerfile — IslamiAI Production
FROM python:3.12-slim

WORKDIR /app

# Install deps dulu (layer cache-friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Non-root user (security best practice)
RUN adduser --disabled-password --gecos "" islamiai
USER islamiai

EXPOSE 8080

# Gunicorn: 2-4 workers per CPU, timeout 30s
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
