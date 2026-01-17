# ccdemo

A Python SMS management application with web UI and REST API.

## Features

- **SMS Composition & Sending**: Create and send SMS messages to single or multiple recipients
- **Message History**: Track sent messages with status (pending, sent, failed)
- **User Management**: Admin interface for user CRUD operations
- **Authentication**: Web login and API token-based authentication
- **Hong Kong Time**: Built-in timezone conversion (UTC to HKT)
- **Mock HKT API**: Testing mode simulates HKT SMS gateway

## Development Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python run.py
```

The app will start on `http://localhost:3570`

## Mock SMS Provider

To run the mock HKT SMS provider (required for testing):

```bash
source .venv/bin/activate
python scripts/mock_hkt_api.py
```

The mock server runs on `http://127.0.0.1:5555/gateway/gateway.jsp`

## Default Admin Account

A fixed admin account is created on first run:

| Field | Value |
|-------|--------|
| Username | `SMSadmin` |
| Password | `SMSpass#12` |
| Role | Admin |
| Status | Active |

Use this account to access the Admin panel for user management.

## API Usage

### Login

```bash
curl -X POST http://localhost:3570/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"SMSadmin","password":"SMSpass#12"}'
```

Response:
```json
{
  "access_token": "k99KnlhEmot8evXjoucEmoMBAkrjeDFowzdNKLoZDfATi4Dj47...",
  "user_id": 1,
  "username": "SMSadmin"
}
```

### Authenticated Request

Use the `access_token` in the Authorization header:

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:3570/api/sms
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Login and get API token |
| `/api/auth/logout` | POST | Logout |
| `/api/sms` | GET | List messages |
| `/api/sms` | POST | Send single SMS |
| `/api/sms/send-bulk` | POST | Send bulk SMS |
| `/api/sms/<id>` | GET | Get message details |
| `/api/sms/<id>/recipients` | GET | Get message recipients |

## Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_example.py

# Lint
ruff check .

# Format
ruff format .
```

## Project Structure

```
ccdemo/
├── src/                    # Source code
│   └── ccdemo/
│       ├── models.py        # Database models (User, Message, Recipient)
│       ├── api/            # REST API endpoints
│   │   ├── auth.py        # Authentication
│   │   └── sms.py         # SMS endpoints
│   ├── web/            # Web UI
│   │   ├── auth.py        # Login/register
│   │   ├── sms.py         # SMS composition/history
│   │   ├── admin.py       # User management (admin only)
│   │   └── templates/
│   │       ├── admin/         # Admin templates
│   │       ├── *.html        # Other templates
│       ├── services/       # Business logic
│       └── static/         # CSS, JS assets
├── tests/                 # Pytest tests
├── scripts/               # Utility scripts
└── pyproject.toml         # Project config
```

## Database

SQLite database (`sms.db`) is auto-created on first run.

To reset the database:
```bash
rm instance/sms.db
# Then restart the app
```

## Configuration

Configuration is in `src/ccdemo/config.py`:

| Setting | Description | Default |
|---------|-------------|----------|
| `SECRET_KEY` | Flask session key | dev-secret-key |
| `DATABASE_URL` | Database path | sqlite:///sms.db |
| `JWT_SECRET_KEY` | Token signing key | dev-jwt-key |
| `HKT_BASE_URL` | HKT SMS gateway | Mock server URL |
| `HKT_APPLICATION_ID` | HKT app ID | LabourDept |
| `HKT_SENDER_NUMBER` | HKT sender number | 852520702793127 |

Set via environment variables or `.env` file.
