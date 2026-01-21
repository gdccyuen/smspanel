# Retry Logic and Dead Letter Queue Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Add retry logic with exponential backoff to SMS gateway requests and implement a dead letter queue for persisting failed messages.

**Architecture:**
1. Add `tenacity` library for configurable retry logic with exponential backoff
2. Create `DeadLetterMessage` model to persist failed SMS for later reprocessing
3. Update worker loop to capture failed tasks and store in dead letter queue
4. Add admin interface to view and retry dead letter messages

**Tech Stack:** Flask, SQLAlchemy, tenacity (retry library), threading

---

### Task 1: Add tenacity dependency

**Files:**
- Modify: `pyproject.toml`
- Modify: `requirements.txt`

**Step 1: Write the failing test**

```python
# tests/test_retry.py
def test_tenacity_available():
    """Tenacity library should be available for retry logic."""
    import tenacity
    assert tenacity is not None
    # Check version has retry decorator
    assert hasattr(tenacity, "retry")
    assert hasattr(tenacity, "stop_after_attempt")
    assert hasattr(tenacity, "wait_exponential")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_retry.py::test_tenacity_available -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Add tenacity to dependencies**

```toml
# pyproject.toml - add under [project]
dependencies = [
    "flask>=3.0.0",
    "flask-sqlalchemy>=3.1.0",
    "flask-login>=0.6.3",
    "flask-wtf>=1.2.1",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "pyjwt>=2.8.0",
    "tenacity>=8.2.0",  # ADD THIS LINE
]
```

```txt
# requirements.txt - add line
tenacity>=8.2.0
```

**Step 4: Install the package**

Run: `pip install tenacity>=8.2.0`

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_retry.py::test_tenacity_available -v`
Expected: PASS

**Step 6: Commit**

```bash
git add pyproject.toml requirements.txt
git commit -m "deps: add tenacity for retry logic"
```

---

### Task 2: Add retry decorator to SMS service

**Files:**
- Modify: `src/smspanel/services/hkt_sms.py:1-77`

**Step 1: Write the failing test**

```python
# tests/test_retry.py
from unittest.mock import patch, MagicMock
from requests.exceptions import ConnectionError, Timeout

def test_send_single_retries_on_connection_error(app):
    """send_single should retry on connection errors."""
    from smspanel.config import ConfigService
    from smspanel.services.hkt_sms import HKTSMSService

    call_count = []

    def mock_post(*args, **kwargs):
        call_count.append(args)
        if len(call_count) < 3:
            raise ConnectionError("Simulated connection error")
        return MagicMock(status_code=200, text="SUCCESS", raise_for_status=MagicMock())

    with patch("smspanel.services.hkt_sms.requests.post", side_effect=mock_post):
        config_service = ConfigService(
            base_url="https://test.com", application_id="test-app", sender_number="12345"
        )
        service = HKTSMSService(config_service)
        result = service.send_single("85212345678", "Test message")

        # Should succeed after retries
        assert result["success"] is True
        # Should have called post 3 times (2 failures + 1 success)
        assert len(call_count) == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_retry.py::test_send_single_retries_on_connection_error -v`
Expected: FAIL - only 1 call, no retry

**Step 3: Add retry decorator to send_single**

```python
# src/smspanel/services/hkt_sms.py
"""SMS service for sending SMS messages."""

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from typing import Dict, Optional

from ..config import ConfigService, SMSConfig


class SMSError(Exception):
    """Exception raised for SMS service errors."""

    pass


class HKTSMSService:
    """Service for interacting with SMS API."""

    def __init__(self, config_service: ConfigService):
        """Initialize SMS service.

        Args:
            config_service: Configuration service for SMS settings.
        """
        self.config_service = config_service
        self._config: Optional[SMSConfig] = None

    def _get_config(self) -> SMSConfig:
        """Get SMS configuration from config service."""
        if self._config is None:
            self._config = self.config_service.get_sms_config()
        return self._config

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        reraise=True,
    )
    def send_single(self, recipient: str, message: str) -> Dict[str, any]:
        """Send a single SMS message with retry logic.

        Args:
            recipient: Phone number (e.g., "85212345678")
            message: SMS content (supports UTF-8)

        Returns:
            Dict with status and response details.

        Raises:
            SMSError: If API request fails after all retries.
        """
        config = self._get_config()

        data = {
            "application": config.application_id,
            "mrt": recipient,
            "sender": config.sender_number,
            "msg_utf8": message,
        }

        try:
            response = requests.post(
                config.base_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )

            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "response_text": response.text,
            }
        except (requests.ConnectionError, requests.Timeout) as e:
            # Let tenacity handle retry
            raise
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
                if hasattr(e, "response")
                else None,
            }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_retry.py::test_send_single_retries_on_connection_error -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/smspanel/services/hkt_sms.py
git commit -m "feat: add retry logic with exponential backoff to SMS service"
```

---

### Task 3: Create DeadLetterMessage model

**Files:**
- Create: `src/smspanel/models/dead_letter.py`
- Modify: `src/smspanel/models.py`

**Step 1: Write the failing test**

```python
# tests/test_dead_letter.py
def test_dead_letter_message_model_exists():
    """DeadLetterMessage model should exist."""
    from smspanel.models.dead_letter import DeadLetterMessage

    assert DeadLetterMessage is not None
    # Check required columns
    assert hasattr(DeadLetterMessage, "id")
    assert hasattr(DeadLetterMessage, "message_id")
    assert hasattr(DeadLetterMessage, "recipient")
    assert hasattr(DeadLetterMessage, "content")
    assert hasattr(DeadLetterMessage, "error_message")
    assert hasattr(DeadLetterMessage, "retry_count")
    assert hasattr(DeadLetterMessage, "created_at")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dead_letter.py::test_dead_letter_message_model_exists -v`
Expected: FAIL - module not found

**Step 3: Create DeadLetterMessage model**

```python
# src/smspanel/models/dead_letter.py
"""Dead letter queue model for failed SMS messages."""

from datetime import datetime, timezone
from . import db


class DeadLetterMessage(db.Model):
    """Model for persisting failed SMS messages for later reprocessing.

    This serves as a dead letter queue where SMS messages that fail
    after all retry attempts are stored for manual review and retry.
    """

    __tablename__ = "dead_letter_messages"

    id = db.Column(db.Integer, primary_key=True)
    # Reference to original message
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=True, index=True)
    # Recipient information
    recipient = db.Column(db.String(20), nullable=False, index=True)
    # Message content
    content = db.Column(db.Text, nullable=False)
    # Error details
    error_message = db.Column(db.Text, nullable=True)
    error_type = db.Column(db.String(50), nullable=True)  # e.g., "ConnectionError", "Timeout"
    # Retry tracking
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    # Status
    status = db.Column(
        db.String(20), default="pending", index=True
    )  # pending, retried, abandoned
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    retried_at = db.Column(db.DateTime, nullable=True)
    last_attempt_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<DeadLetterMessage {self.id}: {self.recipient} ({self.status})>"

    def can_retry(self) -> bool:
        """Check if this message can be retried."""
        return self.retry_count < self.max_retries and self.status == "pending"

    def increment_retry(self) -> None:
        """Increment retry counter and update timestamp."""
        self.retry_count += 1
        self.last_attempt_at = datetime.now(timezone.utc)

    def mark_retried(self) -> None:
        """Mark this message as successfully retried."""
        self.status = "retried"
        self.retried_at = datetime.now(timezone.utc)

    def mark_abandoned(self) -> None:
        """Mark this message as abandoned after max retries."""
        self.status = "abandoned"
```

```python
# src/smspanel/models.py - add at end
from .models.dead_letter import DeadLetterMessage

__all__ = ["User", "Message", "Recipient", "DeadLetterMessage"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dead_letter.py::test_dead_letter_message_model_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/smspanel/models/dead_letter.py src/smspanel/models.py
git commit -m "feat: add DeadLetterMessage model for failed SMS"
```

---

### Task 4: Create dead letter queue service

**Files:**
- Create: `src/smspanel/services/dead_letter.py`

**Step 1: Write the failing test**

```python
# tests/test_dead_letter.py
def test_dead_letter_service_exists(app):
    """DeadLetterQueue service should exist."""
    from smspanel.services.dead_letter import DeadLetterQueue

    with app.app_context():
        dlq = DeadLetterQueue()
        assert dlq is not None

def test_dead_letter_queue_add(app):
    """DeadLetterQueue should be able to add failed messages."""
    from smspanel.services.dead_letter import DeadLetterQueue
    from smspanel.models.dead_letter import DeadLetterMessage

    with app.app_context():
        db.create_all()
        dlq = DeadLetterQueue()
        dlq.add(
            message_id=1,
            recipient="85212345678",
            content="Test message",
            error_message="Connection timeout",
            error_type="Timeout",
        )

        # Verify message was added
        count = DeadLetterMessage.query.count()
        assert count == 1

        # Verify message details
        msg = DeadLetterMessage.query.first()
        assert msg.recipient == "85212345678"
        assert msg.content == "Test message"
        assert msg.error_message == "Connection timeout"
        assert msg.status == "pending"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dead_letter.py::test_dead_letter_service_exists -v`
Expected: FAIL - module not found

**Step 3: Create dead letter queue service**

```python
# src/smspanel/services/dead_letter.py
"""Dead letter queue service for persisting failed SMS messages."""

import logging
from datetime import datetime, timezone
from typing import Optional, List

from ..models import db, DeadLetterMessage

logger = logging.getLogger(__name__)


class DeadLetterQueue:
    """Service for managing dead letter queue of failed SMS messages."""

    def __init__(self, max_retries: int = 3):
        """Initialize dead letter queue service.

        Args:
            max_retries: Maximum number of retry attempts before abandoning.
        """
        self.max_retries = max_retries

    def add(
        self,
        message_id: Optional[int],
        recipient: str,
        content: str,
        error_message: str,
        error_type: str,
    ) -> DeadLetterMessage:
        """Add a failed message to the dead letter queue.

        Args:
            message_id: ID of the original message (if any).
            recipient: Phone number of recipient.
            content: SMS message content.
            error_message: Description of the error.
            error_type: Type of error (e.g., "ConnectionError").

        Returns:
            The created DeadLetterMessage instance.
        """
        dead_letter = DeadLetterMessage(
            message_id=message_id,
            recipient=recipient,
            content=content,
            error_message=error_message,
            error_type=error_type,
            retry_count=0,
            max_retries=self.max_retries,
            status="pending",
        )

        db.session.add(dead_letter)
        db.session.commit()

        logger.info(f"Added failed SMS to dead letter queue: {dead_letter}")
        return dead_letter

    def get_pending(self, limit: int = 100) -> List[DeadLetterMessage]:
        """Get all pending messages ready for retry.

        Args:
            limit: Maximum number of messages to return.

        Returns:
            List of pending DeadLetterMessage instances.
        """
        return (
            DeadLetterMessage.query.filter_by(status="pending")
            .filter(DeadLetterMessage.retry_count < DeadLetterMessage.max_retries)
            .order_by(DeadLetterMessage.created_at.asc())
            .limit(limit)
            .all()
        )

    def get_all(self, status: Optional[str] = None, limit: int = 100) -> List[DeadLetterMessage]:
        """Get all dead letter messages, optionally filtered by status.

        Args:
            status: Optional status filter ("pending", "retried", "abandoned").
            limit: Maximum number of messages to return.

        Returns:
            List of DeadLetterMessage instances.
        """
        query = DeadLetterMessage.query

        if status:
            query = query.filter_by(status=status)

        return query.order_by(DeadLetterMessage.created_at.desc()).limit(limit).all()

    def retry(self, dead_letter_id: int) -> bool:
        """Mark a dead letter message for retry.

        Args:
            dead_letter_id: ID of the dead letter message.

        Returns:
            True if marked for retry, False if max retries exceeded.
        """
        dead_letter = DeadLetterMessage.query.get(dead_letter_id)
        if not dead_letter:
            logger.warning(f"Dead letter message {dead_letter_id} not found")
            return False

        if not dead_letter.can_retry():
            logger.warning(f"Dead letter {dead_letter_id} cannot be retried (retry_count={dead_letter.retry_count})")
            return False

        dead_letter.increment_retry()
        db.session.commit()

        logger.info(f"Dead letter {dead_letter_id} marked for retry (attempt {dead_letter.retry_count})")
        return True

    def mark_retried(self, dead_letter_id: int) -> bool:
        """Mark a dead letter message as successfully retried.

        Args:
            dead_letter_id: ID of the dead letter message.

        Returns:
            True if marked successfully, False if not found.
        """
        dead_letter = DeadLetterMessage.query.get(dead_letter_id)
        if not dead_letter:
            return False

        dead_letter.mark_retried()
        db.session.commit()

        logger.info(f"Dead letter {dead_letter_id} marked as retried")
        return True

    def mark_abandoned(self, dead_letter_id: int) -> bool:
        """Mark a dead letter message as abandoned.

        Args:
            dead_letter_id: ID of the dead letter message.

        Returns:
            True if marked successfully, False if not found.
        """
        dead_letter = DeadLetterMessage.query.get(dead_letter_id)
        if not dead_letter:
            return False

        dead_letter.mark_abandoned()
        db.session.commit()

        logger.info(f"Dead letter {dead_letter_id} marked as abandoned")
        return True

    def get_stats(self) -> dict:
        """Get statistics about the dead letter queue.

        Returns:
            Dict with counts by status.
        """
        pending = DeadLetterMessage.query.filter_by(status="pending").count()
        retried = DeadLetterMessage.query.filter_by(status="retried").count()
        abandoned = DeadLetterMessage.query.filter_by(status="abandoned").count()

        return {
            "pending": pending,
            "retried": retried,
            "abandoned": abandoned,
            "total": pending + retried + abandoned,
        }


# Global dead letter queue instance
_dead_letter_queue: Optional[DeadLetterQueue] = None


def get_dead_letter_queue() -> DeadLetterQueue:
    """Get the global dead letter queue instance.

    Returns:
        The global DeadLetterQueue instance.
    """
    global _dead_letter_queue
    if _dead_letter_queue is None:
        _dead_letter_queue = DeadLetterQueue()
    return _dead_letter_queue


def init_dead_letter_queue(app, max_retries: int = 3):
    """Initialize the dead letter queue with Flask app.

    Args:
        app: Flask application instance.
        max_retries: Maximum retry attempts before abandoning.
    """
    global _dead_letter_queue
    _dead_letter_queue = DeadLetterQueue(max_retries=max_retries)

    # Create tables
    with app.app_context():
        db.create_all()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dead_letter.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/smspanel/services/dead_letter.py
git commit -m "feat: add dead letter queue service"
```

---

### Task 5: Integrate dead letter queue into task queue workers

**Files:**
- Modify: `src/smspanel/services/queue.py`

**Step 1: Write the failing test**

```python
# tests/test_dead_letter.py
def test_task_queue_captures_failures_to_dead_letter(app):
    """Task queue should capture failed tasks to dead letter queue."""
    from smspanel.services.queue import TaskQueue, init_task_queue
    from smspanel.services.dead_letter import get_dead_letter_queue
    from smspanel.models.dead_letter import DeadLetterMessage

    def failing_task():
        raise RuntimeError("Simulated task failure")

    with app.app_context():
        init_task_queue(app, num_workers=1, max_queue_size=10)
        dlq = get_dead_letter_queue()

        # Add a failing task
        queue = get_task_queue()
        queue.enqueue(failing_task)

        # Wait for task to be processed
        import time
        time.sleep(2)

        # Stop queue
        queue.stop()

        # Check dead letter queue
        count = DeadLetterMessage.query.count()
        assert count == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dead_letter.py::test_task_queue_captures_failures_to_dead_letter -v`
Expected: FAIL - dead letter not captured

**Step 3: Modify task queue to capture failures**

```python
# src/smspanel/services/queue.py - modify _worker_loop method
def _worker_loop(self, worker_id: int):
    """Main worker loop for processing tasks.

    Args:
        worker_id: Worker thread ID for logging.
    """
    from .dead_letter import get_dead_letter_queue

    logger.info(f"Worker {worker_id} started")
    while self.running:
        try:
            task_func, args, kwargs = self.queue.get(timeout=1.0)
            try:
                with self.app.app_context():
                    task_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Task execution error in worker {worker_id}: {e}", exc_info=True)
                # Try to capture to dead letter queue
                try:
                    dlq = get_dead_letter_queue()
                    dlq.add(
                        message_id=None,
                        recipient=str(args) if args else "unknown",
                        content=str(kwargs) if kwargs else str(task_func),
                        error_message=str(e),
                        error_type=type(e).__name__,
                    )
                except Exception as dlq_error:
                    logger.error(f"Failed to capture to dead letter queue: {dlq_error}")
            finally:
                self.queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
    logger.info(f"Worker {worker_id} stopped")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dead_letter.py::test_task_queue_captures_failures_to_dead_letter -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/smspanel/services/queue.py
git commit -m "feat: integrate dead letter queue into task workers"
```

---

### Task 6: Add dead letter queue admin web interface

**Files:**
- Create: `src/smspanel/web/dead_letter.py`
- Modify: `src/smspanel/web/__init__.py`

**Step 1: Write the failing test**

```python
# tests/test_dead_letter.py
def test_dead_letter_admin_routes_exist(app):
    """Admin routes for dead letter should exist."""
    from smspanel.web.dead_letter import dead_letter_bp

    assert dead_letter_bp is not None

    # Check route registration
    routes = [rule.rule for rule in dead_letter_bp.url_map.iter_rules()]
    assert "/admin/dead-letter" in routes
    assert "/admin/dead-letter/retry" in routes
    assert "/admin/dead-letter/abandon" in routes
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dead_letter.py::test_dead_letter_admin_routes_exist -v`
Expected: FAIL - module not found

**Step 3: Create admin web routes**

```python
# src/smspanel/web/dead_letter.py
"""Admin routes for dead letter queue management."""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.wrappers import Response

from ..services.dead_letter import get_dead_letter_queue
from ..models.dead_letter import DeadLetterMessage
from ..constants.messages import (
    AUTH_ADMIN_REQUIRED,
    AUTH_LOGIN_REQUIRED,
)
from ..utils.database import db_transaction

web_dead_letter_bp = Blueprint("web_dead_letter", __name__, url_prefix="/admin/dead-letter")


def admin_required(f):
    """Decorator to require admin access."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash(AUTH_LOGIN_REQUIRED, "error")
            return redirect(url_for("web.web_auth.login"))
        if not current_user.is_admin:
            flash(AUTH_ADMIN_REQUIRED, "error")
            return redirect(url_for("web.web_sms.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


@web_dead_letter_bp.route("")
@login_required
@admin_required
def list_dead_letter():
    """List all dead letter messages."""
    status = request.args.get("status")
    dlq = get_dead_letter_queue()
    stats = dlq.get_stats()

    messages = dlq.get_all(status=status, limit=100)

    return render_template(
        "admin/dead_letter.html",
        messages=messages,
        stats=stats,
        current_status=status,
    )


@web_dead_letter_bp.route("/retry/<int:message_id>", methods=["POST"])
@login_required
@admin_required
def retry_dead_letter(message_id: int):
    """Retry a dead letter message."""
    dlq = get_dead_letter_queue()

    if dlq.retry(message_id):
        flash(f"Dead letter {message_id} queued for retry.", "success")
    else:
        flash(f"Dead letter {message_id} cannot be retried (max retries exceeded).", "error")

    return redirect(url_for("web_dead_letter.list_dead_letter"))


@web_dead_letter_bp.route("/abandon/<int:message_id>", methods=["POST"])
@login_required
@admin_required
def abandon_dead_letter(message_id: int):
    """Mark a dead letter message as abandoned."""
    dlq = get_dead_letter_queue()

    if dlq.mark_abandoned(message_id):
        flash(f"Dead letter {message_id} marked as abandoned.", "info")
    else:
        flash(f"Dead letter {message_id} not found.", "error")

    return redirect(url_for("web_dead_letter.list_dead_letter"))


@web_dead_letter_bp.route("/retry-all", methods=["POST"])
@login_required
@admin_required
def retry_all_dead_letter():
    """Retry all pending dead letter messages."""
    dlq = get_dead_letter_queue()
    messages = dlq.get_pending()

    retry_count = 0
    for msg in messages:
        if dlq.retry(msg.id):
            retry_count += 1

    flash(f"{retry_count} dead letter messages queued for retry.", "success")
    return redirect(url_for("web_dead_letter.list_dead_letter"))
```

**Step 4: Register blueprint in web __init__.py**

```python
# src/smspanel/web/__init__.py
from .auth import web_auth_bp
from .sms import web_sms_bp
from .admin import web_admin_bp
from .dead_letter import web_dead_letter_bp  # ADD THIS

__all__ = ["web_auth_bp", "web_sms_bp", "web_admin_bp", "web_dead_letter_bp"]
```

```python
# src/smspanel/app.py - in _register_blueprints
def _register_blueprints(app: Flask) -> None:
    from .api import api_bp
    from .web import web_bp, web_dead_letter_bp  # Add web_dead_letter_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(web_bp)
    app.register_blueprint(web_dead_letter_bp)  # Add this line
```

**Step 5: Create admin template**

```html
<!-- src/smspanel/templates/admin/dead_letter.html -->
{% extends "base.html" %}

{% block title %}Dead Letter Queue - SMS Application{% endblock %}

{% block content %}
<div class="admin-dead-letter">
    <div class="admin-header">
        <h1>Dead Letter Queue</h1>
        <p>Messages that failed after all retry attempts</p>
    </div>

    <!-- Stats Cards -->
    <div class="stats-cards">
        <div class="stat-card pending">
            <h3>{{ stats.pending }}</h3>
            <p>Pending</p>
        </div>
        <div class="stat-card retried">
            <h3>{{ stats.retried }}</h3>
            <p>Retried</p>
        </div>
        <div class="stat-card abandoned">
            <h3>{{ stats.abandoned }}</h3>
            <p>Abandoned</p>
        </div>
        <div class="stat-card total">
            <h3>{{ stats.total }}</h3>
            <p>Total</p>
        </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
        <a href="{{ url_for('web_dead_letter.list_dead_letter') }}"
           class="btn {{ 'btn-primary' if not current_status else 'btn-secondary' }}">
            All
        </a>
        <a href="{{ url_for('web_dead_letter.list_dead_letter', status='pending') }}"
           class="btn {{ 'btn-primary' if current_status == 'pending' else 'btn-secondary' }}">
            Pending
        </a>
        <a href="{{ url_for('web_dead_letter.list_dead_letter', status='retried') }}"
           class="btn {{ 'btn-primary' if current_status == 'retried' else 'btn-secondary' }}">
            Retried
        </a>
        <a href="{{ url_for('web_dead_letter.list_dead_letter', status='abandoned') }}"
           class="btn {{ 'btn-primary' if current_status == 'abandoned' else 'btn-secondary' }}">
            Abandoned
        </a>

        {% if current_status == 'pending' %}
        <form action="{{ url_for('web_dead_letter.retry_all_dead_letter') }}" method="POST" style="display: inline;">
            <button type="submit" class="btn btn-primary"
                    onclick="return confirm('Retry all pending messages?')">
                Retry All Pending
            </button>
        </form>
        {% endif %}
    </div>

    <!-- Dead Letter Table -->
    <div class="table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Recipient</th>
                    <th>Content</th>
                    <th>Error</th>
                    <th>Retries</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for msg in messages %}
                <tr class="status-{{ msg.status }}">
                    <td>{{ msg.id }}</td>
                    <td>{{ msg.recipient }}</td>
                    <td>{{ msg.content[:50] }}{% if msg.content|length > 50 %}...{% endif %}</td>
                    <td>{{ msg.error_message[:50] }}{% if msg.error_message and msg.error_message|length > 50 %}...{% endif %}</td>
                    <td>{{ msg.retry_count }}/{{ msg.max_retries }}</td>
                    <td>
                        <span class="status-badge {{ msg.status }}">{{ msg.status }}</span>
                    </td>
                    <td>{{ msg.created_at|hkt }}</td>
                    <td>
                        {% if msg.status == 'pending' and msg.can_retry() %}
                        <form action="{{ url_for('web_dead_letter.retry_dead_letter', message_id=msg.id) }}" method="POST">
                            <button type="submit" class="btn btn-sm btn-primary">Retry</button>
                        </form>
                        {% endif %}

                        {% if msg.status == 'pending' %}
                        <form action="{{ url_for('web_dead_letter.abandon_dead_letter', message_id=msg.id) }}" method="POST">
                            <button type="submit" class="btn btn-sm btn-secondary"
                                    onclick="return confirm('Abandon this message?')">
                                Abandon
                            </button>
                        </form>
                        {% endif %}
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="8" class="empty-state">No dead letter messages found.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/test_dead_letter.py::test_dead_letter_admin_routes_exist -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/smspanel/web/dead_letter.py src/smspanel/web/__init__.py src/smspanel/app.py
git add src/smspanel/templates/admin/dead_letter.html
git commit -m "feat: add admin UI for dead letter queue management"
```

---

### Task 7: Run full test suite and lint

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
git commit -m "chore: run tests and lint after retry and dead letter queue implementation"
```

---

### Task 8: Update documentation

**Files:**
- Modify: `README.md`

**Step 1: Add documentation for retry and dead letter queue**

```markdown
## Retry Logic

The SMS service uses exponential backoff retry logic for transient failures:

- **Max Attempts**: 3 retries per message
- **Backoff**: Exponential with 2s minimum, 10s maximum
- **Retried Errors**: Connection errors, timeouts

Retry logic is implemented using the `tenacity` library.

## Dead Letter Queue

Failed SMS messages that cannot be delivered after all retry attempts are stored in the dead letter queue for later review and manual retry.

### Accessing Dead Letter Queue

1. Log in as admin
2. Navigate to `/admin/dead-letter`

### Dead Letter Queue Features

- **View All**: Browse all failed messages with filtering by status
- **Retry Individual**: Retry specific failed messages
- **Retry All**: Retry all pending messages at once
- **Abandon**: Mark messages as permanently failed

### Message Status

| Status | Description |
|--------|-------------|
| `pending` | Ready for retry |
| `retried` | Successfully resent |
| `abandoned` | Permanently failed after max retries |
```
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document retry logic and dead letter queue"
```
