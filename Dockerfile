# Production image for long-running public deployment (Render / Fly / Docker)
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOHHOT_DEBUG=0 \
    HOHHOT_DATA_MODE=DEMO \
    PORT=8080

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

# Ensure demo DB exists; regenerate if missing
RUN python -c "from pathlib import Path; import sqlite3; p=Path('hohhot_pm25.db'); print('db', p.exists(), p.stat().st_size if p.exists() else 0)"

EXPOSE 8080

CMD gunicorn -b 0.0.0.0:${PORT} --workers 2 --timeout 120 app:app
