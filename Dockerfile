FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build tools for psycopg2 and Node.js for the frontend
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/cv-filter-fe/package*.json /app/frontend/cv-filter-fe/
RUN npm --prefix /app/frontend/cv-filter-fe ci

COPY . /app

EXPOSE 8000 5173

CMD ["sh", "-c", "npm --prefix /app/frontend/cv-filter-fe run dev -- --host 0.0.0.0 --port 5173 & python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
