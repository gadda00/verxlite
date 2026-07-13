# Verxlite

> **The Universal AI Workflow Agent for Sales & Ops**

Verxlite automates repetitive workflows across email, CRM, and documents—follow-ups, logging, approvals, and summaries—for any industry.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (optional)
- PostgreSQL (Supabase recommended)
- Redis
- Google Cloud Project (for OAuth)
- HubSpot Developer Account (for OAuth)

### Local Development

#### 1. Clone the Repository

```bash
git clone https://github.com/bobmbili82-lgtm/verxlite.git
cd verxlite
```

#### 2. Set Up Infrastructure

You can use Docker Compose for local development:

```bash
# Start PostgreSQL and Redis
docker-compose up -d db redis

# Initialize the database
docker-compose exec api python scripts/init_db.py
```

Or set up services manually:

- **PostgreSQL**: Create a database named `verxlite`
- **Redis**: Run Redis server on localhost:6379

#### 3. Configure Environment Variables

Copy the example environment files and update with your credentials:

```bash
# Backend
cp api/.env.example api/.env
# Edit api/.env with your database URL, OAuth credentials, etc.

# Frontend
cp web/.env.local.example web/.env.local
# Edit web/.env.local with your API URL and Clerk credentials
```

#### 4. Install Dependencies

```bash
# Backend
cd api
poetry install

# Frontend
cd ../web
npm install
```

#### 5. Set Up OAuth Applications

**Google Cloud**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Calendar API and Gmail API
4. Create OAuth 2.0 credentials
5. Add `http://localhost:8000/connections/google/callback` as authorized redirect URI
6. Update `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `api/.env`

**HubSpot**:
1. Go to [HubSpot Developer Portal](https://developers.hubspot.com/)
2. Create a new application
3. Add `http://localhost:8000/connections/hubspot/callback` as redirect URL
4. Update `HUBSPOT_CLIENT_ID` and `HUBSPOT_CLIENT_SECRET` in `api/.env`

**Clerk** (for authentication):
1. Go to [Clerk Dashboard](https://dashboard.clerk.com/)
2. Create a new application
3. Update `CLERK_SECRET_KEY` and `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` in respective `.env` files

#### 6. Set Up Langfuse (Observability)

1. Go to [Langfuse Cloud](https://cloud.langfuse.com/)
2. Create a new project
3. Update `LANGFUSE_SECRET_KEY` and `LANGFUSE_PUBLIC_KEY` in `api/.env`

#### 7. Run the Application

In separate terminals:

```bash
# Backend
cd api
poetry run uvicorn main:app --reload

# Frontend
cd web
npm run dev

# Worker (optional for local testing)
cd worker
poetry run celery -A tasks worker --loglevel=info
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Docker Development

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📁 Project Structure

```
verxlite/
├── api/                          # FastAPI Backend
│   ├── main.py                   # API entry point
│   ├── verxlite_api/             # Backend package
│   │   ├── config.py             # Configuration
│   │   ├── db/                   # Database models and session
│   │   ├── models/               # SQLAlchemy models
│   │   ├── routes/               # API routes
│   │   ├── services/             # Business logic
│   │   ├── connectors/           # External service connectors
│   │   ├── agent/                # LangGraph workflows
│   │   └── observability/        # Langfuse and metrics
│   └── Dockerfile                # Backend Dockerfile
│
├── worker/                       # Celery Worker
│   ├── tasks.py                  # Celery tasks
│   └── Dockerfile                # Worker Dockerfile
│
├── web/                          # Next.js Frontend
│   ├── app/                      # Next.js pages
│   ├── components/               # React components
│   ├── lib/                      # Utilities
│   └── Dockerfile                # Frontend Dockerfile
│
├── scripts/                      # Utility scripts
│   └── init_db.py                # Database initialization
│
├── tests/                        # Tests
│   └── test_workflow_engine.py   # Workflow engine tests
│
├── docs/                         # Documentation
│   └── ARCHITECTURE.md           # Architecture documentation
│
├── docker-compose.yml            # Docker Compose configuration
├── .github/                      # GitHub Actions
│   └── workflows/                # CI/CD pipelines
│       └── ci-cd.yml             # CI/CD configuration
│
└── README.md                     # This file
```

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login a user |
| GET | `/auth/me` | Get current user |
| GET | `/connections` | List connections |
| GET | `/connections/google/authorize` | Start Google OAuth |
| GET | `/connections/google/callback` | Google OAuth callback |
| GET | `/connections/hubspot/authorize` | Start HubSpot OAuth |
| GET | `/connections/hubspot/callback` | HubSpot OAuth callback |
| DELETE | `/connections/{connection_id}` | Delete a connection |
| GET | `/workflows` | List workflows |
| POST | `/workflows/{workflow_id}/runs` | Trigger a workflow run |
| GET | `/workflows/runs/{run_id}` | Get workflow run details |
| GET | `/workflows/runs` | List workflow runs |
| GET | `/artifacts` | List artifacts |
| GET | `/artifacts/{artifact_id}` | Get artifact details |

## 📊 Features

### Core Capabilities

1. **Connectors**
   - Google Workspace (Gmail, Calendar, Drive)
   - HubSpot CRM
   - Salesforce CRM (coming soon)
   - Outlook/Exchange (coming soon)

2. **Agent Logic**
   - Multi-step workflow orchestration
   - LLM-based reasoning and decision making
   - Tool use (API calls, data processing)
   - Structured JSON output

3. **Universal Workflows**
   - Post-meeting followup (MVP)
   - Lead assignment and follow-up
   - Support ticket triage
   - Approval workflows
   - Weekly summaries

4. **Observability**
   - Langfuse tracing for all workflows
   - Token usage tracking
   - Latency monitoring
   - Error tracking and debugging

### Workflow Types

| Workflow | Description | Status |
|----------|-------------|--------|
| Post-Meeting Followup | Auto-log to CRM + draft follow-up email + create tasks | ✅ MVP |
| Lead Assignment | Assign new leads to reps + automated follow-up sequence | 🚧 Coming Soon |
| Support Triage | Triage incoming emails + suggest replies + update ticket status | 🚧 Coming Soon |
| Approval Workflow | Route approval requests + chase approvers + log outcomes | 🚧 Coming Soon |
| Weekly Summary | Compile pipeline/project summaries from CRM + emails | 🚧 Coming Soon |

## 🔧 Configuration

### Backend (`api/.env`)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/verxlite

# Redis
REDIS_URL=redis://localhost:6379/0

# Auth (Clerk)
CLERK_SECRET_KEY=your_clerk_secret_key

# OAuth - Google
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/connections/google/callback

# OAuth - HubSpot
HUBSPOT_CLIENT_ID=your_hubspot_client_id
HUBSPOT_CLIENT_SECRET=your_hubspot_client_secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/connections/hubspot/callback

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

### Frontend (`web/.env.local`)

```env
# API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Clerk Auth
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key

# Environment
NEXT_PUBLIC_ENVIRONMENT=development
```

## 🚀 Deployment

### Production Deployment

#### 1. Set Up Infrastructure

- **Frontend**: Deploy to Vercel
- **Backend**: Deploy to Fly.io or Render
- **Database**: Use Supabase or managed PostgreSQL
- **Queue**: Use Redis on Fly.io or Upstash
- **Observability**: Use hosted Langfuse

#### 2. Configure Environment Variables

Update all environment variables with production credentials.

#### 3. Deploy

```bash
# Frontend (Vercel)
vercel

# Backend (Fly.io)
flyctl deploy

# Worker (Fly.io)
flyctl deploy --app verxlite-worker
```

#### 4. Set Up CI/CD

The repository includes GitHub Actions for CI/CD:
- Automated testing on pull requests
- Docker image building on main branch
- Deployment to production

### Docker Production

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write tests for new features
- Update documentation for changes
- Keep commits atomic and well-described

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [Next.js](https://nextjs.org/)
- AI workflows with [LangGraph](https://langchain-ai.github.io/langgraph/)
- Observability by [Langfuse](https://langfuse.com/)
- UI components from [Shadcn UI](https://ui.shadcn.com/)

## 📞 Support

- Documentation: [https://docs.verxlite.dev](https://docs.verxlite.dev) (coming soon)
- Issues: [GitHub Issues](https://github.com/bobmbili82-lgtm/verxlite/issues)
- Email: support@verxlite.dev

---

**Verxlite - The weight of manual work, lifted.**
