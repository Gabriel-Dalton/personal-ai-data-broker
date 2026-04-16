# Personal AI Data Broker

A **local-first** platform that puts you in control of what personal data AI services can access. Instead of handing your information directly to every AI tool, the Data Broker acts as a secure intermediary — you store data once, define granular access policies, issue scoped API keys, and maintain a complete audit trail of every request.

## Why?

AI assistants and plugins increasingly ask for personal context — contacts, calendar events, preferences, health data, and more. Today you either share everything or nothing. The Personal AI Data Broker gives you a middle ground:

| Problem | Solution |
|---|---|
| AI tools get blanket access to your data | Fine-grained **access policies** per service |
| No visibility into what was shared | **Full audit log** of every request |
| Hard to revoke access after sharing | **One-click key revocation** — instant cutoff |
| Data scattered across services | **Single local vault** you control |

## Features

- **Data Vault** — store personal data entries organised by category (contacts, health, finance, preferences, etc.) with optional sensitivity flags
- **Access Policies** — define which categories each AI service can read, whether sensitive entries are included, and rate limits
- **Scoped API Keys** — generate keys tied to specific policies; each AI integration gets only the permissions it needs
- **Broker API** — a single `/broker/query` endpoint that AI services call; the broker enforces policies and returns only permitted data
- **Audit Log** — every access attempt (allowed or denied) is logged with timestamps, IP addresses, and details
- **Web Dashboard** — a clean, modern UI to manage everything from your browser
- **Auto-generated API docs** — interactive Swagger UI at `/docs`

## Quick Start

### Prerequisites

- Python 3.11+

### 1. Clone & install

```bash
git clone https://github.com/Gabriel-Dalton/personal-ai-data-broker.git
cd personal-ai-data-broker
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure (optional)

```bash
cp .env.example .env
# Edit .env to set a strong SECRET_KEY and admin password
```

### 3. Run

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) to see the landing page, or go straight to the [dashboard](http://localhost:8000/dashboard).

Default credentials: **admin** / **changeme** (change these in `.env` before production use).

### Docker

```bash
docker build -t ai-data-broker .
docker run -p 8000:8000 ai-data-broker
```

## Usage

### Step 1 — Add your data

In the **Data Vault** tab, create entries like:

| Category | Label | Content | Sensitive |
|---|---|---|---|
| contacts | Work email | alice@company.com | No |
| health | Blood type | O+ | Yes |
| preferences | Favourite cuisine | Japanese | No |

### Step 2 — Create a policy

In **Access Policies**, create a policy such as:

- **Name:** ChatGPT — Read contacts  
- **Allowed categories:** `contacts,preferences`  
- **Allow sensitive:** No  
- **Rate limit:** 60/hr  

### Step 3 — Issue an API key

In **API Keys**, generate a key tied to that policy. Copy the key — it's shown only once.

### Step 4 — AI service queries the broker

The AI service sends a POST request to the broker endpoint:

```bash
curl -X POST http://localhost:8000/broker/query \
  -H "Authorization: Bearer pdb_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"categories": ["contacts"], "include_sensitive": false}'
```

Response:

```json
{
  "allowed": true,
  "data": [
    { "category": "contacts", "label": "Work email", "content": "alice@company.com" }
  ],
  "filtered_count": 1,
  "policy_name": "ChatGPT — Read contacts"
}
```

### Step 5 — Review the audit log

Every query (allowed or denied) is recorded and visible in the **Audit Log** tab.

## API Reference

Interactive docs are available at `/docs` (Swagger UI) and `/redoc` when the server is running.

### Core Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | — | Get a bearer token |
| GET | `/api/data` | Bearer | List data entries |
| POST | `/api/data` | Bearer | Create data entry |
| PATCH | `/api/data/{id}` | Bearer | Update data entry |
| DELETE | `/api/data/{id}` | Bearer | Delete data entry |
| GET | `/api/policies` | Bearer | List policies |
| POST | `/api/policies` | Bearer | Create policy |
| PATCH | `/api/policies/{id}` | Bearer | Update policy |
| DELETE | `/api/policies/{id}` | Bearer | Delete policy |
| GET | `/api/keys` | Bearer | List API keys |
| POST | `/api/keys` | Bearer | Create API key |
| DELETE | `/api/keys/{id}` | Bearer | Revoke API key |
| POST | `/broker/query` | API Key | Query data (AI-facing) |
| GET | `/api/audit` | Bearer | View audit logs |

## Project Structure

```
personal-ai-data-broker/
├── app/
│   ├── main.py              # FastAPI application & lifespan
│   ├── config.py             # Settings (env-based)
│   ├── database.py           # SQLAlchemy engine & session
│   ├── models.py             # ORM models
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── auth.py               # JWT & password hashing
│   ├── routers/
│   │   ├── auth_router.py    # Login
│   │   ├── data_router.py    # Data vault CRUD
│   │   ├── policy_router.py  # Access policies CRUD
│   │   ├── apikey_router.py  # API key management
│   │   ├── broker_router.py  # AI-facing broker endpoint
│   │   ├── audit_router.py   # Audit log viewing
│   │   └── dashboard_router.py  # Web UI routes
│   ├── templates/            # Jinja2 HTML templates
│   └── static/               # Static assets
├── tests/
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## Security Notes

- All data is stored locally in SQLite — nothing leaves your machine unless an AI service queries the broker and the policy permits it.
- Passwords are hashed with bcrypt.
- Dashboard authentication uses short-lived JWTs.
- API keys use a `pdb_` prefix and are generated with `secrets.token_urlsafe`.
- **Change the default admin password** before exposing the service to any network.

## License

MIT
