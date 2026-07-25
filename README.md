# Applywise

AI-powered job application tracker for students and early-career professionals.

## Tech Stack

- **Backend:** Django 5, Django REST Framework, PostgreSQL, Redis, Celery
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui
- **AI:** Multi-provider LLM support (Gemini, OpenAI, Claude)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 22+ (for frontend development outside Docker)
- Python 3.13+ (for backend development outside Docker)

### Setup

```bash
# Clone and enter project
cd applywise

# Copy environment variables
cp .env.example .env

# Start all services
docker compose up --build
```

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000/api/
- **Django Admin:** http://localhost:8000/admin/

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py runserver
```

**Redis:**
```bash
sudo service redis-server start
# then type 
redis-cli
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
applywise/
├── backend/          # Django API
│   ├── config/       # Settings, URLs, ASGI/WSGI
│   └── apps/         # Django applications
├── frontend/         # React SPA
│   └── src/          # Source code
└── docker-compose.yml
```

## License

Proprietary - All rights reserved.
