# Verxlite Development Guide

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **Docker** (optional) - [Download Docker](https://www.docker.com/get-started)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Poetry** (Python dependency manager) - Install with `pip install poetry`

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bobmbili82-lgtm/verxlite.git
   cd verxlite
   ```

2. **Set up the backend:**
   ```bash
   cd api
   poetry install
   ```

3. **Set up the frontend:**
   ```bash
   cd ../web
   npm install
   ```

4. **Start the services:**
   ```bash
   # In one terminal - start database and Redis
   docker-compose up -d db redis
   
   # In another terminal - start the backend
   cd api
   poetry run uvicorn main:app --reload
   
   # In another terminal - start the frontend
   cd ../web
   npm run dev
   ```

5. **Access the application:**
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📁 Project Structure

```
verxlite/
├── api/                          # FastAPI Backend
│   ├── main.py                   # API entry point
│   ├── verxlite_api/             # Backend package
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration settings
│   │   ├── db/                   # Database models and session
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Base model
│   │   │   └── session.py        # Database session
│   │   ├── models/               # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py
│   │   │   ├── user.py
│   │   │   ├── connection.py
│   │   │   ├── workflow.py
│   │   │   ├── workflow_run.py
│   │   │   ├── workflow_step.py
│   │   │   └── artifact.py
│   │   ├── schemas/              # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── error.py
│   │   │   ├── auth.py
│   │   │   ├── tenant.py
│   │   │   ├── user.py
│   │   │   ├── connection.py
│   │   │   ├── workflow.py
│   │   │   ├── workflow_run.py
│   │   │   └── artifact.py
│   │   ├── routes/               # API routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── connections.py
│   │   │   ├── workflows.py
│   │   │   └── artifacts.py
│   │   ├── services/             # Business logic
│   │   │   ├── __init__.py
│   │   │   └── workflow_engine.py
│   │   ├── connectors/           # External service connectors
│   │   │   ├── __init__.py
│   │   │   ├── google.py
│   │   │   └── hubspot.py
│   │   ├── agent/                # LangGraph workflows
│   │   │   └── __init__.py
│   │   ├── observability/        # Observability (Langfuse, metrics)
│   │   │   ├── __init__.py
│   │   │   ├── langfuse.py
│   │   │   └── metrics.py
│   │   └── utils/                # Utilities
│   │       ├── __init__.py
│   │       ├── encryption.py
│   │       └── logger.py
│   ├── pyproject.toml            # Python dependencies
│   ├── .env.example              # Environment variables template
│   └── Dockerfile
│
├── worker/                       # Celery Worker
│   ├── tasks.py                  # Celery tasks
│   ├── __init__.py
│   ├── pyproject.toml            # Python dependencies
│   └── Dockerfile
│
├── web/                          # Next.js Frontend
│   ├── app/                      # Next.js pages (App Router)
│   │   ├── globals.css           # Global styles
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Landing page
│   │   ├── dashboard/            # Dashboard page
│   │   │   └── page.tsx
│   │   ├── login/                # Login page
│   │   │   └── page.tsx
│   │   ├── sign-up/              # Sign up page
│   │   │   └── [[...sign-up]]/
│   │   │       └── page.tsx
│   │   ├── settings/             # Settings page
│   │   │   └── page.tsx
│   │   ├── connections/          # Connections page
│   │   │   └── page.tsx
│   │   └── workflows/            # Workflows page
│   │       └── page.tsx
│   ├── components/               # React components
│   │   └── ui/                  # Shadcn UI components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── badge.tsx
│   │       ├── table.tsx
│   │       ├── input.tsx
│   │       ├── label.tsx
│   │       ├── switch.tsx
│   │       ├── alert.tsx
│   │       └── skeleton.tsx
│   ├── lib/                      # Utilities
│   │   └── utils.ts
│   ├── public/                   # Static files
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── postcss.config.js
│   └── Dockerfile
│
├── scripts/                      # Utility scripts
│   └── init_db.py                # Database initialization
│
├── tests/                        # Tests
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── test_models.py
│   ├── test_services.py
│   └── test_routes.py
│
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # System architecture
│   └── DEVELOPMENT_GUIDE.md      # This file
│
├── migrations/                   # Database migrations
│   ├── __init__.py
│   ├── env.py
│   └── script.py.mako
│
├── docker-compose.yml            # Docker Compose configuration
├── .github/                      # GitHub Actions
│   └── workflows/
│       └── ci-cd.yml             # CI/CD pipeline
│
├── README.md                     # Project overview
├── IMPLEMENTATION_SUMMARY.md     # Implementation summary
└── AUDIT_CHECKLIST.md            # Audit checklist
```

## 🔧 Configuration

### Environment Variables

#### Backend (`api/.env`)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/verxlite

# Redis
REDIS_URL=redis://localhost:6379/0

# Auth (Clerk)
CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key

# OAuth - Google
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/connections/google/callback

# OAuth - HubSpot
HUBSPOT_CLIENT_ID=your_hubspot_client_id
HUBSPOT_CLIENT_SECRET=your_hubspot_client_secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/connections/hubspot/callback

# Frontend URL (for OAuth redirects)
FRONTEND_URL=http://localhost:3000

# LLM Providers
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Observability (Langfuse)
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_HOST=https://cloud.langfuse.com

# Environment
ENVIRONMENT=development
DEBUG=true

# Encryption
ENCRYPTION_KEY=your_encryption_key
```

#### Frontend (`web/.env.local`)

```env
# API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Clerk Auth
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key

# Environment
NEXT_PUBLIC_ENVIRONMENT=development
```

### Setting Up OAuth Applications

#### Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the following APIs:
   - Google Calendar API
   - Gmail API
   - Google Drive API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized JavaScript origins: `http://localhost:3000`
   - Authorized redirect URIs: `http://localhost:8000/connections/google/callback`
5. Copy the Client ID and Client Secret to your `.env` file

#### HubSpot

1. Go to [HubSpot Developer Portal](https://developers.hubspot.com/)
2. Create a new application
3. Add the redirect URL: `http://localhost:8000/connections/hubspot/callback`
4. Copy the Client ID and Client Secret to your `.env` file

#### Clerk

1. Go to [Clerk Dashboard](https://dashboard.clerk.com/)
2. Create a new application
3. Copy the Publishable Key and Secret Key to your `.env` files

#### Langfuse

1. Go to [Langfuse Cloud](https://cloud.langfuse.com/)
2. Create a new project
3. Copy the Secret Key and Public Key to your `.env` file

## 🛠 Development Workflow

### Backend Development

1. **Add a new model:**
   - Create a new file in `api/verxlite_api/models/`
   - Import and add to `api/verxlite_api/models/__init__.py`
   - Run `alembic revision --autogenerate -m "Add new model"`
   - Run `alembic upgrade head` to apply migrations

2. **Add a new route:**
   - Create or modify a file in `api/verxlite_api/routes/`
   - Import and add to `api/verxlite_api/routes/__init__.py`
   - Import and mount the router in `api/main.py`

3. **Add a new service:**
   - Create a new file in `api/verxlite_api/services/`
   - Import and add to `api/verxlite_api/services/__init__.py`

4. **Add a new connector:**
   - Create a new file in `api/verxlite_api/connectors/`
   - Import and add to `api/verxlite_api/connectors/__init__.py`

### Frontend Development

1. **Add a new page:**
   - Create a new file in `web/app/` (following Next.js App Router conventions)
   - Add navigation links in the header

2. **Add a new component:**
   - Create a new file in `web/components/ui/`
   - Export from `web/components/ui/index.ts` (if needed)

3. **Add a new utility:**
   - Create a new file in `web/lib/`

### Running Tests

```bash
# Run all tests
cd api
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_models.py -v

# Run with coverage
poetry run pytest tests/ --cov=verxlite_api --cov-report=html
```

### Database Migrations

```bash
# Generate a new migration
cd api
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Downgrade migrations
alembic downgrade -1

# Show migration history
alembic history
```

## 📊 API Documentation

The API is documented using OpenAPI/Swagger. When running the backend in development mode, you can access the interactive API documentation at:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### API Endpoints

#### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login a user |
| GET | `/auth/me` | Get current user |

#### Connections

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/connections/` | List all connections |
| GET | `/connections/{connection_id}` | Get a specific connection |
| POST | `/connections/google/authorize` | Start Google OAuth flow |
| GET | `/connections/google/callback` | Google OAuth callback |
| POST | `/connections/hubspot/authorize` | Start HubSpot OAuth flow |
| GET | `/connections/hubspot/callback` | HubSpot OAuth callback |
| POST | `/connections/{connection_id}/refresh` | Refresh connection token |
| POST | `/connections/{connection_id}/sync` | Sync connection data |
| DELETE | `/connections/{connection_id}` | Delete a connection |

#### Workflows

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workflows/` | List all workflows |
| POST | `/workflows/` | Create a new workflow |
| GET | `/workflows/{workflow_id}` | Get a specific workflow |
| PUT | `/workflows/{workflow_id}` | Update a workflow |
| DELETE | `/workflows/{workflow_id}` | Delete a workflow |
| POST | `/workflows/{workflow_id}/runs` | Trigger a workflow run |
| GET | `/workflows/runs/{run_id}` | Get workflow run details |
| GET | `/workflows/runs` | List workflow runs |
| GET | `/workflows/stats` | Get workflow statistics |
| GET | `/workflows/templates` | List workflow templates |
| POST | `/workflows/{workflow_id}/enable` | Enable a workflow |
| POST | `/workflows/{workflow_id}/disable` | Disable a workflow |

#### Artifacts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/artifacts/` | List all artifacts |
| GET | `/artifacts/{artifact_id}` | Get a specific artifact |

#### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API root |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |

## 🎨 Frontend Development

### Styling

The frontend uses **Tailwind CSS** for styling with the following configuration:

- **Colors:** Defined in `web/tailwind.config.ts`
- **Components:** Shadcn UI components in `web/components/ui/`
- **Brand Colors:** Verxlite neon blue (#00f5ff) and dark theme

### Adding a New Page

1. Create a new file in `web/app/` (e.g., `web/app/new-page/page.tsx`)
2. Add the page to the navigation in the header
3. Use existing components from `web/components/ui/`

### Using Shadcn UI

To add a new Shadcn UI component:

```bash
cd web
npx shadcn-ui@latest add [component-name]
```

For example:
```bash
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add select
npx shadcn-ui@latest add checkbox
```

### Authentication

The frontend uses **Clerk** for authentication. To use authentication in a page:

```tsx
"use client";

import { useUser } from "@clerk/nextjs";

export default function ProtectedPage() {
  const { isSignedIn, user, isLoaded } = useUser();
  
  if (!isLoaded) {
    return <div>Loading...</div>;
  }
  
  if (!isSignedIn) {
    return <div>Please sign in</div>;
  }
  
  return (
    <div>Welcome, {user.fullName}!</div>
  );
}
```

## 🚀 Deployment

### Local Development with Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

#### Frontend (Vercel)

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Deploy:
   ```bash
   cd web
   vercel
   ```

3. Follow the prompts to link your Vercel account and deploy

#### Backend (Fly.io)

1. Install Fly.io CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. Login:
   ```bash
   flyctl auth login
   ```

3. Create a new app:
   ```bash
   cd api
   flyctl apps create verxlite-api
   ```

4. Deploy:
   ```bash
   flyctl deploy
   ```

#### Database (Supabase)

1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Create a new project
3. Get the connection string and add to your environment variables

#### Queue (Upstash Redis)

1. Go to [Upstash Console](https://console.upstash.com/)
2. Create a new Redis database
3. Get the connection URL and add to your environment variables

### Environment Variables for Production

Update all environment variables with production credentials:

- Database URL (Supabase)
- Redis URL (Upstash)
- OAuth credentials (Google, HubSpot)
- LLM API keys (Anthropic, OpenAI)
- Clerk keys
- Langfuse keys
- Encryption key (generate a secure one)

## 🔍 Debugging

### Backend Debugging

1. **Enable debug mode:**
   ```env
   DEBUG=true
   ```

2. **View logs:**
   ```bash
   cd api
   poetry run uvicorn main:app --reload --log-level debug
   ```

3. **Use Python debugger:**
   ```python
   import pdb; pdb.set_trace()
   ```

### Frontend Debugging

1. **View browser console:**
   - Open Chrome DevTools (F12)
   - Check the Console tab for errors

2. **Debug Next.js:**
   ```bash
   cd web
   npm run dev
   ```

3. **Use React DevTools:**
   - Install [React DevTools](https://react.dev/learn/react-developer-tools) browser extension

### Database Debugging

1. **Connect to PostgreSQL:**
   ```bash
   psql -h localhost -U postgres -d verxlite
   ```

2. **View tables:**
   ```sql
   \dt
   ```

3. **Query data:**
   ```sql
   SELECT * FROM tenants;
   ```

## 📝 Coding Standards

### Python

- Follow **PEP 8** style guide
- Use **type hints** for all functions and variables
- Use **snake_case** for variable and function names
- Use **PascalCase** for class names
- Use **UPPER_CASE** for constants
- Keep lines under **100 characters**
- Use **4 spaces** for indentation
- Use **double quotes** for strings

### TypeScript

- Follow **TypeScript best practices**
- Use **type annotations** for all variables and functions
- Use **PascalCase** for component names
- Use **camelCase** for variable and function names
- Use **UPPER_CASE** for constants
- Keep lines under **100 characters**
- Use **2 spaces** for indentation
- Use **single quotes** for strings

### SQLAlchemy

- Use **declarative base** for models
- Use **snake_case** for table and column names
- Add **indexes** for frequently queried columns
- Use **relationships** for foreign keys
- Add **docstrings** to models and methods

### FastAPI

- Use **Pydantic models** for request/response validation
- Add **docstrings** to routes
- Use **dependency injection** for database sessions
- Add **tags** to routes for API documentation
- Use **HTTP status codes** appropriately

### React

- Use **TypeScript** for all components
- Use **functional components** with hooks
- Use **PascalCase** for component names
- Use **props** for component configuration
- Add **PropTypes** or TypeScript types for props
- Use **Shadcn UI** components when possible

## 🧪 Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py               # Pytest fixtures
├── test_models.py            # Model tests
├── test_services.py          # Service tests
├── test_routes.py            # Route tests
└── test_integration.py       # Integration tests
```

### Writing Tests

1. **Model Tests:** Test model creation, methods, and properties
2. **Service Tests:** Test business logic with mocked dependencies
3. **Route Tests:** Test API endpoints with TestClient
4. **Integration Tests:** Test interactions between components

### Running Tests

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_models.py -v

# Run specific test
poetry run pytest tests/test_models.py::TestTenantModel::test_tenant_creation -v

# Run with coverage
poetry run pytest tests/ --cov=verxlite_api --cov-report=html
```

### Test Coverage

Aim for **80%+ test coverage** for all modules. Use `pytest-cov` to measure coverage:

```bash
poetry add --group dev pytest-cov
poetry run pytest tests/ --cov=verxlite_api --cov-report=html
```

## 📚 Resources

### Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Shadcn UI Documentation](https://ui.shadcn.com/docs)
- [Clerk Documentation](https://clerk.com/docs)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Langfuse Documentation](https://langfuse.com/docs)

### Tools

- [Python Type Checker (mypy)](https://mypy-lang.org/)
- [Python Linter (ruff)](https://github.com/astral-sh/ruff)
- [Python Formatter (black)](https://github.com/psf/black)
- [TypeScript Type Checker](https://www.typescriptlang.org/docs/handbook/type-checking.html)
- [ESLint](https://eslint.org/)
- [Prettier](https://prettier.io/)

### Community

- [FastAPI GitHub](https://github.com/tiangolo/fastapi)
- [Next.js GitHub](https://github.com/vercel/next.js)
- [Tailwind CSS GitHub](https://github.com/tailwindlabs/tailwindcss)
- [Shadcn UI GitHub](https://github.com/shadcn/ui)

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/your-feature`
3. **Commit your changes:** `git commit -m 'Add some feature'`
4. **Push to the branch:** `git push origin feature/your-feature`
5. **Open a Pull Request**

### Pull Request Guidelines

- Follow the **coding standards**
- Add **tests** for new features
- Update **documentation** for changes
- Keep **commits atomic** and well-described
- Use **conventional commits** format
- Add a **description** of the changes
- Link to any **related issues**

### Commit Message Format

```
type(scope): subject

body

footer
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(workflows): add post-meeting followup workflow

- Add workflow definition for post-meeting followup
- Add steps for fetching calendar event and CRM contact
- Add LLM reasoning for meeting analysis
- Add actions for creating CRM note, email, and task

Closes #123
```

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

## 🙏 Support

- **Documentation:** [https://docs.verxlite.dev](https://docs.verxlite.dev) (coming soon)
- **Issues:** [GitHub Issues](https://github.com/bobmbili82-lgtm/verxlite/issues)
- **Email:** support@verxlite.dev

---

**Happy coding!** 🎉

*Verxlite - The weight of manual work, lifted.*
