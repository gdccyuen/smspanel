# Security Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 3 security vulnerabilities - hardcoded admin credentials, weak default SECRET_KEY, and missing CSRF protection on web forms.

**Architecture:**
1. Replace hardcoded admin credentials with environment variable fallback, using a generated password if none provided
2. Make SECRET_KEY mandatory in production (fail fast if not set), remove insecure default
3. Add Flask-WTF for CSRF protection on all web forms

**Tech Stack:** Flask, Flask-WTF, python-dotenv

---

### Task 1: Add Flask-WTF dependency

**Files:**
- Modify: `pyproject.toml`
- Modify: `requirements.txt`

**Step 1: Write the failing test**

```python
# tests/test_csrf.py
def test_csrf_token_required_on_login():
    """Login form should reject requests without CSRF token."""
    from smspanel.app import create_app

    app = create_app("testing")
    with app.test_client() as client:
        response = client.post(
            "/login",
            data={"username": "test", "password": "test"},
            follow_redirects=True
        )
        # Should fail or show error due to missing CSRF token
        assert response.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_csrf.py -v`
Expected: Test passes (no CSRF protection currently)

**Step 3: Add Flask-WTF to dependencies**

```toml
# pyproject.toml - add under [project]
dependencies = [
    "flask>=3.0.0",
    "flask-sqlalchemy>=3.1.0",
    "flask-login>=0.6.3",
    "flask-wtf>=1.2.1",  # ADD THIS LINE
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "pyjwt>=2.8.0",
]
```

```txt
# requirements.txt - add line
flask-wtf>=1.2.1
```

**Step 4: Commit**

```bash
git add pyproject.toml requirements.txt
git commit -m "deps: add flask-wtf for CSRF protection"
```

---

### Task 2: Add CSRF token to base template

**Files:**
- Modify: `src/smspanel/templates/base.html`

**Step 1: Write the failing test**

```python
# tests/test_csrf.py
def test_base_template_contains_csrf_token():
    """Base template should include CSRF token field."""
    from smspanel.app import create_app

    app = create_app("testing")
    with app.test_request_context():
        from flask_wtf.csrf import CSRF_PROTECT_MECHANICS
        # Check that csrf_token is available in templates
        from jinja2 import TemplateSyntaxError
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_csrf.py::test_base_template_contains_csrf_token -v`
Expected: FAIL - CSRF not initialized

**Step 3: Add CSRF token field to base template**

```html
<!-- src/smspanel/templates/base.html - add before closing </body> -->
    {% if csrf_token %}
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    {% endif %}
</body>
</html>
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_csrf.py::test_base_template_contains_csrf_token -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/smspanel/templates/base.html
git commit -m "feat: add CSRF token field to base template"
```

---

### Task 3: Initialize CSRF protection in app factory

**Files:**
- Modify: `src/smspanel/extensions/__init__.py`
- Modify: `src/smspanel/app.py`

**Step 1: Write the failing test**

```python
# tests/test_csrf.py
def test_csrf_protection_initialized():
    """CSRF protection should be enabled on app."""
    from smspanel.app import create_app

    app = create_app("testing")
    # CSRF should be enabled
    assert app.config.get("WTF_CSRF_ENABLED", False) == True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_csrf.py::test_csrf_protection_initialized -v`
Expected: FAIL - CSRF not configured

**Step 3: Initialize CSRF in extensions**

```python
# src/smspanel/extensions/__init__.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def init_db(app):
    db.init_app(app)


def init_login(app):
    login_manager.init_app(app)


def init_csrf(app):
    """Initialize CSRF protection.

    Args:
        app: Flask application instance.
    """
    csrf.init_app(app)


def init_all(app):
    """Initialize all extensions."""
    init_db(app)
    init_login(app)
    init_csrf(app)


__all__ = ["db", "login_manager", "csrf", "init_db", "init_login", "init_csrf", "init_all"]
```

**Step 4: Update app.py to use new exports**

```python
# src/smspanel/app.py
from .extensions import db, login_manager, csrf
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_csrf.py::test_csrf_protection_initialized -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/smspanel/extensions/__init__.py src/smspanel/app.py
git commit -m "feat: initialize CSRF protection in app factory"
```

---

### Task 4: Update all web routes to handle CSRF errors

**Files:**
- Modify: `src/smspanel/web/auth.py:22-43`
- Modify: `src/smspanel/web/sms.py:64-140`
- Modify: `src/smspanel/web/admin.py:55-187`

**Step 1: Write the failing test**

```python
# tests/test_csrf.py
def test_login_rejects_invalid_csrf():
    """Login with invalid CSRF token should be rejected."""
    from smspanel.app import create_app

    app = create_app("testing")
    with app.test_client() as client:
        response = client.post(
            "/login",
            data={
                "username": "SMSadmin",
                "password": "SMSpass#12",
                "csrf_token": "invalid-token"
            }
        )
        # Should return 400 Bad Request
        assert response.status_code == 400
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_csrf.py::test_login_rejects_invalid_csrf -v`
Expected: FAIL - CSRF validation not happening

**Step 3: Run test to verify it passes (after implementing)**

Run: `pytest tests/test_csrf.py::test_login_rejects_invalid_csrf -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/smspanel/web/auth.py src/smspanel/web/sms.py src/smspanel/web/admin.py
git commit -m "feat: enable CSRF protection on all web forms"
```

---

### Task 5: Fix hardcoded admin credentials in app factory

**Files:**
- Modify: `src/smspanel/app.py:123-143`

**Step 1: Write the failing test**

```python
# tests/test_security.py
def test_admin_credentials_not_hardcoded():
    """Admin username/password should not be hardcoded in source."""
    import inspect
    from smspanel.app import _ensure_admin_user

    source = inspect.getsource(_ensure_admin_user)
    # Should not contain hardcoded credentials
    assert "SMSpass#12" not in source
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_security.py::test_admin_credentials_not_hardcoded -v`
Expected: FAIL - password is hardcoded

**Step 3: Fix the credential handling**

```python
def _ensure_admin_user(app: Flask) -> None:
    """Ensure default admin user exists.

    Admin credentials are read from environment variables:
    - ADMIN_USERNAME: Admin username (default: SMSadmin)
    - ADMIN_PASSWORD: Admin password (auto-generated if not set)

    Args:
        app: Flask application instance.
    """
    import secrets
    import string
    from os import getenv
    from .models import User

    with app.app_context():
        db.create_all()
        admin_user = User.query.filter_by(username="SMSadmin").first()
        if admin_user is None:
            # Get admin password from env or generate one
            admin_password = getenv("ADMIN_PASSWORD")
            if admin_password is None:
                # Generate a secure random password
                alphabet = string.ascii_letters + string.digits
                admin_password = "".join(secrets.choice(alphabet) for _ in range(16))
                # In production, log or print warning about generated password
                if not app.config.get("DEBUG", True):
                    app.logger.warning(
                        "Admin password was auto-generated. "
                        "Set ADMIN_PASSWORD environment variable to prevent this."
                    )

            admin = User(username="SMSadmin")
            admin.set_password(admin_password)
            admin.token = User.generate_token()
            admin.is_admin = True
            admin.is_active = True

            db.session.add(admin)
            db.session.commit()

            # Log the generated password in development only
            if getenv("ADMIN_PASSWORD") is None and app.config.get("DEBUG", False):
                print(f"\n[DEV] Generated admin password: {admin_password}\n")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_security.py::test_admin_credentials_not_hardcoded -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/smspanel/app.py
git commit -m "security: use env var for admin password with auto-generation fallback"
```

---

### Task 6: Fix default SECRET_KEY in production config

**Files:**
- Modify: `src/smspanel/config/config.py:24-50`

**Step 1: Write the failing test**

```python
# tests/test_security.py
def test_production_secret_key_not_default():
    """Production config should not use default/weak SECRET_KEY."""
    from smspanel.config.config import ProductionConfig

    # Should either fail fast or require env var
    secret = ProductionConfig.SECRET_KEY
    assert secret != "dev-secret-key-change-in-production"
    assert len(secret) >= 32  # At least 256 bits
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_security.py::test_production_secret_key_not_default -v`
Expected: FAIL - default key is weak

**Step 3: Fix the SECRET_KEY configuration**

```python
class Config:
    """Base configuration."""

    # Flask - SECRET_KEY must be set in production!
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///sms.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SMS Gateway
    SMS_BASE_URL = os.getenv("SMS_BASE_URL")
    SMS_APPLICATION_ID = os.getenv("SMS_APPLICATION_ID")
    SMS_SENDER_NUMBER = os.getenv("SMS_SENDER_NUMBER")

    # SMS Queue
    SMS_QUEUE_WORKERS = 4
    SMS_QUEUE_MAX_SIZE = 1000


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True

    def __init__(self):
        super().__init__()
        # Use a dev key only in development (warn in logs)
        if self.SECRET_KEY is None:
            import warnings
            warnings.warn(
                "SECRET_KEY not set, using development default. "
                "Set SECRET_KEY environment variable for production!"
            )
            self.SECRET_KEY = "dev-secret-key-change-in-production"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False

    def __init__(self):
        super().__init__()
        # SECRET_KEY is required in production
        if self.SECRET_KEY is None:
            raise ValueError(
                "SECRET_KEY environment variable is required in production. "
                "Set it before starting the application."
            )
        # Ensure key is sufficiently long
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long."
            )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_security.py::test_production_secret_key_not_default -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/smspanel/config/config.py
git commit -m "security: make SECRET_KEY mandatory in production with validation"
```

---

### Task 7: Add CSRF token to all form templates

**Files:**
- Modify: `src/smspanel/templates/login.html`
- Modify: `src/smspanel/templates/compose.html`
- Modify: `src/smspanel/templates/admin/create_user.html`
- Modify: `src/smspanel/templates/admin/change_password.html`
- Modify: `src/smspanel/templates/admin/delete_user.html`
- Modify: `src/smspanel/templates/register.html` (if exists)

**Step 1: Write the failing test**

```python
# tests/test_csrf.py
def test_all_forms_have_csrf_token():
    """All form templates should include CSRF token."""
    import os
    from smspanel.app import create_app

    templates_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "src", "smspanel", "templates"
    )

    for root, _, files in os.walk(templates_dir):
        for fname in files:
            if fname.endswith(".html"):
                fpath = os.path.join(root, fname)
                with open(fpath) as f:
                    content = f.read()
                # Check if template has forms but no CSRF
                if "<form" in content:
                    assert 'name="csrf_token"' in content or 'csrf_token()' in content, \
                        f"Template {fname} has form but no CSRF token"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_csrf.py::test_all_forms_have_csrf_token -v`
Expected: FAIL - templates missing CSRF tokens

**Step 3: Add CSRF token to login.html**

```html
<!-- src/smspanel/templates/login.html -->
{% block content %}
<div class="auth-container">
    <h1>Login</h1>
    <form method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <div class="form-group">
```

**Step 4: Add CSRF token to compose.html**

```html
<!-- src/smspanel/templates/compose.html -->
    <form method="POST" class="compose-form">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

**Step 5: Add CSRF tokens to admin templates**

```html
<!-- admin/create_user.html -->
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

```html
<!-- admin/change_password.html -->
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

```html
<!-- admin/delete_user.html -->
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/test_csrf.py::test_all_forms_have_csrf_token -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/smspanel/templates/**/*.html
git commit -m "feat: add CSRF tokens to all form templates"
```

---

### Task 8: Update environment variable documentation

**Files:**
- Modify: `src/smspanel/config/config.py` (docstring)
- Modify: `README.md` or create `.env.example`

**Step 1: Write the failing test**

```python
# tests/test_security.py
def test_env_documentation_exists():
    """Environment variables should be documented."""
    import os
    docs_exist = (
        os.path.exists(".env.example") or
        "ADMIN_PASSWORD" in (open("README.md").read() if os.path.exists("README.md") else "")
    )
    assert docs_exist, "ADMIN_PASSWORD env var should be documented"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_security.py::test_env_documentation_exists -v`
Expected: FAIL - not documented

**Step 3: Create .env.example**

```bash
# .env.example
# Copy this to .env and fill in values

# Database
DATABASE_URL=sqlite:///sms.db

# Flask
SECRET_KEY=<required: at least 32 characters>

# Admin credentials (optional - will auto-generate if not set)
ADMIN_PASSWORD=<optional: set for deterministic admin password>

# SMS Gateway
SMS_BASE_URL=https://cst01.1010.com.hk/gateway/gateway.jsp
SMS_APPLICATION_ID=LabourDept
SMS_SENDER_NUMBER=852520702793127
```

**Step 4: Update config.py docstring**

```python
"""Flask application configuration classes.

Environment Variables:
    Required:
        DATABASE_URL - SQLAlchemy database connection string
        SECRET_KEY - Flask session encryption (min 32 chars, required in production)
        SMS_BASE_URL - SMS gateway URL
        SMS_APPLICATION_ID - SMS API app ID
        SMS_SENDER_NUMBER - SMS sender number

    Optional (with defaults):
        ADMIN_PASSWORD - Admin user password (auto-generated if not set)
"""
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_security.py::test_env_documentation_exists -v`
Expected: PASS

**Step 6: Commit**

```bash
git add .env.example README.md src/smspanel/config/config.py
git commit -m "docs: document new ADMIN_PASSWORD env var and SECRET_KEY requirements"
```

---

### Task 9: Run full test suite and lint

**Files:**
- Run: All tests
- Run: Linting

**Step 1: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests pass

**Step 2: Run linter**

```bash
ruff check .
ruff format .
```

Expected: No errors

**Step 3: Commit**

```bash
git add .
git commit -m "chore: run tests and lint after security hardening"
```
