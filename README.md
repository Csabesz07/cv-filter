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

## Auth endpoints & screens
- Web screens: `/login/` and `/register/` (responsive, store JWT tokens in `sessionStorage` after success).
- API endpoints:
  - `POST /api/auth/register/` with `username`, `email` (optional), `password`
  - `POST /api/auth/login/` with `username`, `password`
  - Responses include `access` and `refresh` JWT tokens plus user payload.

## Ranking API
- `POST /api/ranking/create/`
   - Body example:
      ```json
      {
         "criteria": {
            "required_skills": ["Python", "Django"],
            "preferred_skills": ["Docker"],
            "min_experience_years": 3,
            "required_level": "bachelor"
         },
         "bias_config": {"skill_weight": 0.6, "experience_weight": 0.3, "education_weight": 0.1},
         "candidate_filters": {"status": ["new", "in_review"]}
      }
      ```
   - Response:
      ```json
      {"ranking_run_id": "<uuid>", "status": "completed", "created_at": "..."}
      ```

- `GET /api/ranking/{run_id}/results/`
   - Returns run metadata and ordered candidate results with `score`, `rank`, `explanation`, `details_json`.
