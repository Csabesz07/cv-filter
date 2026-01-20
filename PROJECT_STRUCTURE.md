# CV Filter - Modern Monorepo Structure

## 📁 Directory Organization

```
cv-filter/
├── 📂 apps/                   # Application Code
│   ├── api/                   # Backend Application
│   │   └── cv_filter/         # Django project
│   │       ├── accounts/      # User accounts & authentication
│   │       ├── ranking/       # CV ranking system
│   │       ├── document_extraction/  # CV text extraction
│   │       ├── entity_extraction/    # Named entity recognition
│   │       ├── summarization/ # CV summarization
│   │       └── manage.py
│   │
│   └── web/                   # Frontend Application
│       ├── app/               # React Router app
│       │   ├── routes/        # Page components
│       │   ├── utils/         # Utilities (auth, etc.)
│       │   └── root.tsx
│       ├── package.json
│       └── vite.config.ts
│
├── 📂 docs/                   # Documentation
│   ├── api/                   # API Documentation
│   │   ├── CV_SUMMARY_API_EXAMPLES.md
│   │   └── RANKING_EVENTS_API.md
│   └── user-guides/           # User Guides & Tutorials
│       ├── AUDIT_LOGGING.md
│       ├── LOGGING_QUICKSTART.md
│       ├── FRONTEND_SUMMARY_INTEGRATION.md
│       └── QUICK_FIX_INSTRUCTIONS.md
│
├── 📂 tests/                  # Test Suite
│   ├── integration/           # Integration & E2E Tests
│   │   ├── test_audit_api.ps1
│   │   ├── test_audit_api.sh
│   │   ├── test_bias_detection.py
│   │   ├── test_ranking_audit.py
│   │   └── test_summary.py
│   └── fixtures/              # Test Fixtures & Data
│
├── 📂 tools/                  # Development Tools
│   ├── check_audit_logs.py
│   ├── check_audit_metadata.py
│   ├── check_business_events.py
│   ├── check_severity.py
│   └── test_token_fix.html
│
├── 📂 project/                # Project Management
│   ├── MVP_REPORT.md
│   ├── TASK_4.2_IMPLEMENTATION.md
│   ├── USER_STORY_III.1.1_STATUS.md
│   └── USER_STORY_III.1.3_IMPLEMENTATION.md
│
├── 📂 samples/                # Sample Data
│   ├── cvs_en/                # English CV samples
│   └── cvs_hu/                # Hungarian CV samples
│
├── 📂 docker/                 # Docker Configuration
│   └── initdb/
│       └── 001-enable-pgvector.sql
│
├── 📂 uploads/                # User Uploads (gitignored)
│
├── 📄 docker-compose.yml      # Service Orchestration
├── 📄 Dockerfile              # Backend Container
├── 📄 requirements.txt        # Python Dependencies
├── 📄 pixi.toml              # Package Manager Config
└── 📄 README.md              # Main README

```

## 🎯 Design Principles

### Monorepo Benefits
- **Single Source of Truth**: All code in one repository
- **Simplified Dependencies**: Shared tooling and configurations
- **Atomic Changes**: Frontend + Backend changes in single commit
- **Clear Boundaries**: Separation between apps, docs, tests, and tools

### Directory Purpose

| Directory | Purpose | What Goes Here |
|-----------|---------|----------------|
| `apps/` | Production code | Backend API, Frontend Web App |
| `docs/` | Technical documentation | API specs, user guides |
| `tests/` | All test code | Integration tests, fixtures |
| `tools/` | Developer utilities | Scripts, debugging tools |
| `project/` | Project management | Reports, user stories, planning |
| `samples/` | Reference data | Sample CVs for testing |

## 🚀 Quick Start

### Development
```bash
# Start all services
docker-compose up

# Access applications
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Django Admin: http://localhost:8000/admin
```

### Running Tests
```bash
# Integration tests
cd tests/integration
python test_bias_detection.py

# PowerShell API test
.\test_audit_api.ps1

# Bash API test
bash test_audit_api.sh
```

### Development Tools
```bash
# Check audit logs
python tools/check_audit_logs.py

# Debug token issues
# Open tools/test_token_fix.html in browser

# Check metadata
python tools/check_audit_metadata.py
```

## 📚 Documentation

- **API Docs**: `docs/api/` - REST API documentation
- **User Guides**: `docs/user-guides/` - How-to guides and tutorials
- **Project Docs**: `project/` - Implementation reports and status

## 🧪 Testing

```bash
# All tests are in tests/integration/
cd tests/integration

# Run specific test
python test_bias_detection.py

# PowerShell tests
.\test_audit_api.ps1
```

## 🔧 Configuration

- `.env` - Environment variables (copy from `.env.example`)
- `docker-compose.yml` - Container orchestration
- `apps/api/cv_filter/settings.py` - Django settings
- `apps/web/vite.config.ts` - Vite configuration

## 📦 Package Management

- **Backend**: `requirements.txt` + `pixi.toml`
- **Frontend**: `apps/web/package.json`

## 🏗️ Architecture

### Backend (`apps/api/`)
- **Framework**: Django 5.2 + Django REST Framework
- **Database**: PostgreSQL + pgvector
- **Authentication**: JWT (SimpleJWT)
- **Features**: CV parsing, ranking, summarization, audit logging

### Frontend (`apps/web/`)
- **Framework**: React 19 + React Router
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Features**: CV management, candidate search, summary generation

## 🔐 Security

- JWT token authentication with auto-refresh
- Token lifetime: 30 min (access), 1 day (refresh)
- Comprehensive audit logging
- Organization-based data isolation
