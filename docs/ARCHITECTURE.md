# Verxlite Architecture

## Overview

Verxlite is a **Universal AI Workflow Agent** that automates repetitive workflows across email, CRM, and documents. This document describes the high-level architecture, components, and data flow.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Verxlite System                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────────┐  │
│  │             │    │             │    │                                 │  │
│  │   Frontend  │    │    Backend  │    │           Worker Queue          │  │
│  │   (Next.js) │    │   (FastAPI)  │    │         (Redis + Celery)         │  │
│  │             │    │             │    │                                 │  │
│  └──────┬──────┘    └──────┬──────┘    └──────────────┬────────────────┘  │
│         │                  │                         │                     │
│         │ REST API         │                         │                     │
│         │ (HTTP/HTTPS)     │                         │                     │
│         ▼                  ▼                         ▼                     │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                                                                     │  │
│  │                        PostgreSQL Database                         │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                                                                     │  │
│  │                      External Services                            │  │
│  │                                                                     │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │  │
│  │  │             │  │             │  │                             │  │  │
│  │  │  Google     │  │  HubSpot    │  │   Other CRMs/Email Providers  │  │  │
│  │  │  Workspace  │  │             │  │                             │  │  │
│  │  │             │  │             │  │                             │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                                                                     │  │
│  │                      Observability Stack                           │  │
│  │                                                                     │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │  │
│  │  │             │  │             │  │                             │  │  │
│  │  │  Langfuse   │  │  Prometheus  │  │         Grafana               │  │  │
│  │  │             │  │             │  │                             │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Frontend (Next.js)

**Purpose**: User interface for managing workflows, connections, and viewing results.

**Technologies**:
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn UI
- Clerk (Authentication)

**Pages**:
- `/` - Landing page
- `/login` - Login page
- `/sign-up` - Sign up page
- `/dashboard` - Main dashboard
- `/workflows` - Workflow management
- `/connections` - Connection management
- `/settings` - User settings

**Responsibilities**:
- User authentication and authorization
- Display workflow runs and their status
- Allow users to connect external services (Google, HubSpot, etc.)
- Provide UI for triggering workflows manually
- Show artifacts (CRM notes, email drafts, tasks)


### 2. Backend (FastAPI)

**Purpose**: REST API for managing users, workflows, connections, and triggering workflow runs.

**Technologies**:
- FastAPI
- Python 3.10+
- SQLAlchemy (ORM)
- PostgreSQL (Database)
- Pydantic (Data validation)
- JWT (Authentication)

**Endpoints**:
- `/auth/*` - Authentication
- `/connections/*` - External service connections
- `/workflows/*` - Workflow management
- `/artifacts/*` - Artifact management
- `/health` - Health check

**Responsibilities**:
- User authentication and authorization
- OAuth flow for external services
- Workflow CRUD operations
- Triggering workflow runs (adds to queue)
- Storing workflow runs and artifacts
- Providing API for frontend


### 3. Worker (Celery)

**Purpose**: Background job processing for workflow execution.

**Technologies**:
- Celery
- Redis (Message broker)
- Python 3.10+

**Tasks**:
- `execute_workflow_run` - Execute a workflow run
- `sync_google_calendar` - Sync Google Calendar events
- `sync_hubspot_contacts` - Sync HubSpot contacts
- `process_webhook_event` - Process webhook events

**Responsibilities**:
- Execute workflows asynchronously
- Handle retries for failed tasks
- Process webhook events from external services
- Sync data from external services


### 4. Database (PostgreSQL)

**Purpose**: Persistent storage for all application data.

**Technologies**:
- PostgreSQL 15+
- SQLAlchemy (ORM)
- Supabase (Managed PostgreSQL)

**Tables**:
- `tenants` - Company/workspace
- `users` - User accounts
- `connections` - OAuth connections to external services
- `workflows` - Workflow definitions
- `workflow_runs` - Workflow execution records
- `workflow_steps` - Individual steps in a workflow run
- `artifacts` - Artifacts created by workflows (CRM notes, emails, tasks)

**Responsibilities**:
- Store all application data
- Provide relationships between entities
- Support filtering and querying


### 5. Observability Stack

**Purpose**: Monitoring, tracing, and metrics for the system.

**Components**:
- **Langfuse**: LLM tracing and evaluation
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization

**Responsibilities**:
- Trace workflow runs and steps
- Track LLM token usage and latency
- Monitor system health and performance
- Provide insights for debugging


## Data Flow

### 1. User Connects External Service

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐
│         │     │             │     │             │
│  User   │────▶│  Frontend   │────▶│   Backend   │
│         │     │             │     │             │
└─────────┘     └─────────────┘     └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │             │
                                       │  External    │
                                       │  Service    │
                                       │  (Google,    │
                                       │   HubSpot)  │
                                       │             │
                                       └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │             │
                                       │  Database   │
                                       │             │
                                       └─────────────┘
```

1. User clicks "Connect Google" in the frontend
2. Frontend redirects to backend OAuth endpoint
3. Backend initiates OAuth flow with Google
4. Google redirects back to backend with authorization code
5. Backend exchanges code for tokens
6. Backend stores connection in database
7. Backend redirects to frontend with success


### 2. Workflow Triggered (Manual)

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐
│         │     │             │     │             │
│  User   │────▶│  Frontend   │────▶│   Backend   │
│         │     │             │     │             │
└─────────┘     └─────────────┘     └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │             │
                                       │    Queue    │
                                       │   (Redis)   │
                                       │             │
                                       └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │             │
                                       │   Worker    │
                                       │  (Celery)   │
                                       │             │
                                       └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │             │
                                       │ External    │
                                       │ Services    │
                                       │             │
                                       └─────────────┘
```

1. User clicks "Run Workflow" in the frontend
2. Frontend sends request to backend
3. Backend creates workflow run record in database
4. Backend adds workflow run to queue
5. Worker picks up workflow run from queue
6. Worker executes workflow steps
7. Worker calls external services as needed
8. Worker updates workflow run status in database


### 3. Workflow Triggered (Automatic - Webhook)

```
┌─────────────────────────────────────────────────────────────┐
│                                                         │
│  ┌─────────────┐                                       │
│  │             │                                       │
│  │ External    │────▶┌─────────────┐    ┌─────────────┐  │
│  │ Service    │    │             │    │             │  │
│  │ (Google    │    │   Backend   │────▶│    Queue    │  │
│  │  Calendar) │    │             │    │   (Redis)   │  │
│  │             │    │             │    │             │  │
│  └─────────────┘    └─────────────┘    └──────┬──────┘  │
│                                                  │        │
│                                                  ▼        │
│                                           ┌─────────────┐  │
│                                           │             │  │
│                                           │   Worker    │  │
│                                           │  (Celery)   │  │
│                                           │             │  │
│                                           └─────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────────┘
```

1. External service (Google Calendar) sends webhook event
2. Backend receives webhook and validates it
3. Backend creates workflow run record in database
4. Backend adds workflow run to queue
5. Worker picks up workflow run from queue
6. Worker executes workflow steps
7. Worker calls external services as needed
8. Worker updates workflow run status in database


## Workflow Execution

### Post-Meeting Followup Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐  │
│  │             │     │             │     │                             │  │
│  │   Trigger   │────▶│  Fetch      │────▶│        LLM Reasoning        │  │
│  │  (Calendar   │     │  Calendar   │     │                             │  │
│  │   Event)    │     │   Event     │     │  - Analyze meeting context    │  │
│  │             │     │             │     │  - Extract action items       │  │
│  └─────────────┘     └─────────────┘     │  - Identify next steps        │  │
│                                          │  - Determine sentiment         │  │
│                                          └──────────────┬──────────────┘  │
│                                                             │              │
│  ┌─────────────────────────────────────────────────────────────┬──────┘
│  │                                                         │              │
│  ▼                                                         ▼              │
│ ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐ │
│ │             │     │             │     │                             │ │
│ │ Create CRM  │     │ Draft       │     │ Create CRM Task             │ │
│ │ Note       │     │ Email       │     │                             │ │
│ │             │     │             │     │                             │ │
│ └─────────────┘     └─────────────┘     └─────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

1. **Trigger**: Calendar event ends
2. **Fetch Calendar Event**: Get meeting details from Google Calendar
3. **Fetch CRM Contact**: Get contact details from HubSpot
4. **LLM Reasoning**: Analyze meeting context and extract:
   - Summary
   - Action items
   - Next steps
   - Sentiment
   - Deal stage
5. **Create CRM Note**: Log summary to HubSpot
6. **Draft Email**: Create follow-up email draft in Gmail
7. **Create CRM Task**: Create task in HubSpot


## Security

### Authentication
- **Frontend**: Clerk for user authentication
- **Backend**: JWT tokens for API authentication
- **Worker**: No direct user access (runs in background)

### Authorization
- Row-level security in PostgreSQL
- All queries filtered by `tenant_id`
- Users can only access their own data

### Data Protection
- OAuth tokens encrypted at rest (Fernet encryption)
- Sensitive data (emails, CRM content) sanitized in logs
- No raw PII stored in observability tools

### Rate Limiting
- 100 requests/minute per tenant for API
- Queue-based processing prevents overload


## Scalability

### Horizontal Scaling
- **Frontend**: Vercel (serverless, auto-scaling)
- **Backend**: FastAPI (can be deployed on multiple instances)
- **Worker**: Celery (multiple workers can process queue)
- **Database**: PostgreSQL (read replicas for scaling)

### Performance
- **Caching**: Redis for rate limiting and temporary data
- **Queue**: Redis for background job processing
- **Async**: All external API calls are async

### Cost Optimization
- **Token Usage**: Track LLM token usage per workflow
- **Model Selection**: Use cheaper models for simple tasks
- **Caching**: Cache frequent LLM calls


## Deployment

### Infrastructure
- **Frontend**: Vercel
- **Backend**: Fly.io / Render
- **Database**: Supabase
- **Queue**: Redis (Fly.io / Upstash)
- **Observability**: Langfuse (hosted)

### CI/CD
- GitHub Actions for testing and deployment
- Docker containers for all services
- Automated deployments on main branch

### Monitoring
- Uptime checks for all services
- Alerts on error spikes or queue backlogs
- DB backups automated
