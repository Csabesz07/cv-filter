# cv-filter

Local development now runs on PostgreSQL with a UUID-based custom user model.

## Quickstart with Docker
1. Copy `.env.example` to `.env` and adjust secrets if needed.
2. Build and start the stack:
   ```bash
   docker-compose up --build
   ```
3. The Django app will run on http://localhost:8000 and auto-apply migrations.

## Without Docker
1. Ensure PostgreSQL is running and export the environment variables from `.env.example`.
2. Install dependencies (e.g. `pip install -r requirements.txt`).
3. Run migrations and start the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
