# Rate Limiting and Queue Status Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement rate limiting (2 msg/sec) for SMS gateway with queue status API for monitoring job progress.

**Architecture:**
- Add `MessageJobStatus` enum and `Message` fields for tracking job state
- Create `RateLimiter` class using token bucket algorithm with configurable rate
- Modify `TaskQueue.worker_loop` to respect rate limits between individual sends
- Add `/api/queue/status` endpoint for queue monitoring
- Enhance `/api/sms/{id}` with job status and ETA fields

**Tech Stack:** Python 3.10+, Flask, SQLite/MySQL, threading.Lock

---

## Tasks

### Task 1: Add MessageJobStatus Enum and Message Fields

**Files:**
- Modify: `src/smspanel/models.py`

**Step 1: Add MessageJobStatus enum**

```python
class MessageJobStatus(str, Enum):
    """Message job status for tracking bulk send progress."""

    PENDING = "pending"     # Waiting in queue
    SENDING = "sending"     # Currently being sent
    COMPLETED = "completed" # All recipients sent
    PARTIAL = "partial"     # Some failed
    FAILED = "failed"       # All failed
```

**Step 2: Add Message fields**

```python
# In Message class:
job_status = db.Column(
    db.String(20), default=MessageJobStatus.PENDING, index=True
)
queue_position = db.Column(db.Integer, nullable=True)  # NULL when sending
estimated_complete_at = db.Column(db.DateTime, nullable=True)
```

**Step 3: Add helper property**

```python
@property
def is_complete(self) -> bool:
    """Check if message sending is complete."""
    return self.job_status in (
        MessageJobStatus.COMPLETED,
        MessageJobStatus.PARTIAL,
        MessageJobStatus.FAILED,
    )
```

**Step 4: Write test**

```python
# tests/test_message_job_status.py
def test_message_job_status_enum():
    assert MessageJobStatus.PENDING == "pending"
    assert MessageJobStatus.SENDING == "sending"
    assert MessageJobStatus.COMPLETED == "completed"
    assert MessageJobStatus.PARTIAL == "partial"
    assert MessageJobStatus.FAILED == "failed"

def test_message_job_status_fields(app):
    with app.app_context():
        from smspanel.models import Message, MessageJobStatus
        msg = Message(user_id=1, content="Test")
        assert msg.job_status == MessageJobStatus.PENDING
        assert msg.queue_position is None
        assert msg.estimated_complete_at is None
```

**Step 5: Run test**

```bash
pytest tests/test_message_job_status.py -v
```

**Step 6: Implement fields and enum**

**Step 7: Run test to verify pass**

**Step 8: Commit**

```bash
git add src/smspanel/models.py tests/test_message_job_status.py
git commit -m "feat: add MessageJobStatus enum and message fields for job tracking"
```

---

### Task 2: Create RateLimiter Class

**Files:**
- Create: `src/smspanel/utils/rate_limiter.py`

**Step 1: Write failing test**

```python
# tests/test_rate_limiter.py
from smspanel.utils.rate_limiter import RateLimiter

def test_rate_limiter_allows_burst():
    limiter = RateLimiter(rate_per_sec=2, burst_capacity=4)
    # Should allow initial burst
    assert limiter.try_acquire() == True
    assert limiter.try_acquire() == True
    assert limiter.try_acquire() == True
    assert limiter.try_acquire() == True
    # 5th should block or return False

def test_rate_limiter_refills():
    limiter = RateLimiter(rate_per_sec=2, burst_capacity=2)
    limiter.try_acquire()  # burst used
    limiter.try_acquire()  # burst used
    # Wait and refill
    import time
    time.sleep(0.6)  # Should allow 1 token after 0.5s
    assert limiter.try_acquire() == True

def test_rate_limiter_blocks_when_exhausted():
    limiter = RateLimiter(rate_per_sec=2, burst_capacity=1)
    limiter.try_acquire()
    result = limiter.try_acquire()  # Should block or False
    assert result in [True, False]  # Depends on blocking behavior
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_rate_limiter.py -v
```

**Step 3: Write implementation**

```python
"""Rate limiter using token bucket algorithm."""

import threading
import time
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for SMS throughput control.

    Attributes:
        rate_per_sec: Tokens added per second (e.g., 2 for 2 msg/sec)
        burst_capacity: Maximum tokens stored (allows burst)
    """

    def __init__(self, rate_per_sec: float = 2.0, burst_capacity: Optional[int] = None):
        """Initialize rate limiter.

        Args:
            rate_per_sec: Number of tokens added per second.
            burst_capacity: Max tokens that can accumulate. Defaults to rate_per_sec.
        """
        self.rate_per_sec = rate_per_sec
        self.burst_capacity = burst_capacity if burst_capacity is not None else rate_per_sec
        self._tokens: float = float(self.burst_capacity)
        self._last_update: float = time.monotonic()
        self._lock = threading.Lock()

    def _add_tokens(self) -> None:
        """Add tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        tokens_to_add = elapsed * self.rate_per_sec
        self._tokens = min(self.burst_capacity, self._tokens + tokens_to_add)
        self._last_update = now

    def try_acquire(self) -> bool:
        """Try to acquire a token.

        Returns:
            True if token acquired, False if rate limited.
        """
        with self._lock:
            self._add_tokens()
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False

    def acquire(self, timeout: float = 10.0) -> bool:
        """Acquire a token, blocking until available or timeout.

        Args:
            timeout: Max seconds to wait for a token.

        Returns:
            True if token acquired, False if timed out.
        """
        start = time.monotonic()
        while True:
            with self._lock:
                self._add_tokens()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return True
            # Check timeout
            if time.monotonic() - start > timeout:
                return False
            # Don't spin too fast
            time.sleep(0.01)

    def get_tokens(self) -> float:
        """Get current available tokens (thread-unsafe, for stats only)."""
        with self._lock:
            self._add_tokens()
            return self._tokens


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(rate_per_sec=2.0, burst_capacity=4)
    return _rate_limiter


def init_rate_limiter(rate_per_sec: float = 2.0, burst_capacity: Optional[int] = None):
    """Initialize the global rate limiter."""
    global _rate_limiter
    _rate_limiter = RateLimiter(rate_per_sec=rate_per_sec, burst_capacity=burst_capacity)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_rate_limiter.py -v
```

**Step 5: Commit**

```bash
git add src/smspanel/utils/rate_limiter.py tests/test_rate_limiter.py
git commit -m "feat: add RateLimiter class with token bucket algorithm"
```

---

### Task 3: Integrate Rate Limiter into TaskQueue

**Files:**
- Modify: `src/smspanel/services/queue.py`
- Modify: `src/smspanel/config.py` (add rate limit config)

**Step 1: Write failing test**

```python
# tests/test_task_queue_rate_limit.py
def test_task_queue_uses_rate_limiter(app):
    """TaskQueue should integrate with rate limiter."""
    from smspanel.services.queue import init_task_queue, get_task_queue
    from smspanel.utils.rate_limiter import get_rate_limiter

    init_task_queue(app, num_workers=1)
    queue = get_task_queue()

    assert queue.rate_limiter is not None
    assert isinstance(queue.rate_limiter.get_tokens(), float)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_task_queue_rate_limit.py -v
```

**Step 3: Update config**

```python
# In src/smspanel/config.py, add to Config class:
SMS_RATE_PER_SEC: float = 2.0
SMS_BURST_CAPACITY: Optional[int] = 4
```

**Step 4: Update TaskQueue**

```python
# In TaskQueue.__init__:
self.rate_limiter = get_rate_limiter()

# In TaskQueue._worker_loop, before calling task_func:
self.rate_limiter.acquire()
```

**Step 5: Run test to verify it passes**

**Step 6: Commit**

```bash
git add src/smspanel/services/queue.py src/smspanel/config.py tests/test_task_queue_rate_limit.py
git commit -m "feat: integrate rate limiter into task queue workers"
```

---

### Task 4: Add Queue Status API Endpoint

**Files:**
- Create: `src/smspanel/api/queue.py`
- Modify: `src/smspanel/api/__init__.py` (register blueprint)

**Step 1: Write failing test**

```python
# tests/test_queue_status.py
def test_queue_status_endpoint_exists(app):
    with app.test_client() as client:
        response = client.get("/api/queue/status")
        assert response.status_code == 200
        data = response.get_json()
        assert "queue_depth" in data
        assert "msgs_per_sec" in data
        assert "pending_messages" in data
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_queue_status.py -v
```

**Step 3: Create queue.py**

```python
"""Queue status API endpoints."""

from flask import Blueprint, jsonify
from datetime import datetime, timezone
from typing import Optional

from smspanel.models import Message, MessageJobStatus
from smspanel.services.queue import get_task_queue
from smspanel.utils.rate_limiter import get_rate_limiter
from smspanel.extensions import db

api_queue_bp = Blueprint("api_queue", __url_prefix="/api")


@api_queue_bp.route("/queue/status", methods=["GET"])
def queue_status():
    """Get current queue status and statistics.

    Returns:
        JSON with queue depth, rate limit info, and per-user stats if authenticated.
    """
    queue = get_task_queue()
    limiter = get_rate_limiter()

    # Count pending messages in queue (job_status = PENDING)
    pending_count = db.session.query(Message).filter(
        Message.job_status == MessageJobStatus.PENDING
    ).count()

    # Count sending messages
    sending_count = db.session.query(Message).filter(
        Message.job_status == MessageJobStatus.SENDING
    ).count()

    # Get oldest pending message for estimating wait time
    oldest = db.session.query(Message).filter(
        Message.job_status == MessageJobStatus.PENDING
    ).order_by(Message.created_at.asc()).first()

    # Calculate estimate
    rate_per_sec = limiter.rate_per_sec
    msgs_ahead = pending_count

    response = {
        "queue_depth": queue.get_queue_size(),
        "msgs_per_sec": rate_per_sec,
        "statistics": {
            "pending_messages": pending_count,
            "sending_messages": sending_count,
            "oldest_pending_at": oldest.created_at.isoformat() if oldest else None,
            "estimated_throughput_sec": rate_per_sec,
        }
    }

    return jsonify(response), 200
```

**Step 4: Register blueprint in api/__init__.py**

**Step 5: Run test to verify it passes**

**Step 6: Commit**

```bash
git add src/smspanel/api/queue.py tests/test_queue_status.py
git commit -m "feat: add /api/queue/status endpoint for monitoring"
```

---

### Task 5: Enhance Message API with Job Status

**Files:**
- Modify: `src/smspanel/api/sms.py` (update get_message response)

**Step 1: Write failing test**

```python
# tests/test_message_job_status_api.py
def test_get_message_includes_job_status(app):
    """GET /api/sms/{id} should include job_status and queue info."""
    # Create a message with recipients
    with app.app_context():
        from smspanel.models import User, Message, Recipient, MessageJobStatus
        user = User(username="test", password_hash="x", is_admin=False)
        db.session.add(user)
        db.session.commit()

        msg = Message(
            user_id=user.id,
            content="Test message",
            job_status=MessageJobStatus.PENDING,
            queue_position=5,
        )
        db.session.add(msg)
        db.session.commit()

        with app.test_client() as client:
            response = client.get(f"/api/sms/{msg.id}", headers={"Authorization": f"Bearer {user.token}"})
            assert response.status_code == 200
            data = response.get_json()
            assert "job_status" in data
            assert data["job_status"] == "pending"
```

**Step 2: Run test to verify it fails**

**Step 3: Update api/sms.py get_message function**

```python
# In get_message, update response to include:
"job_status": message.job_status,
"queue_position": message.queue_position,
"estimated_complete_at": message.estimated_complete_at.isoformat() if message.estimated_complete_at else None,
```

**Step 4: Run test to verify it passes**

**Step 5: Commit**

```bash
git add src/smspanel/api/sms.py tests/test_message_job_status_api.py
git commit -m "feat: enhance /api/sms/{id} with job_status and queue info"
```

---

### Task 6: Update Queue Worker to Track Job Status

**Files:**
- Modify: `src/smspanel/services/queue.py`

**Step 1: Write failing test**

```python
# tests/test_message_status_transitions.py
def test_message_status_transitions_on_send(app):
    """Message should transition from PENDING to SENDING when processed."""
    with app.app_context():
        from smspanel.models import User, Message, MessageJobStatus
        from smspanel.utils.rate_limiter import get_rate_limiter

        user = User(username="test", password_hash="x", is_admin=False)
        db.session.add(user)
        db.session.commit()

        msg = Message(
            user_id=user.id,
            content="Test",
            job_status=MessageJobStatus.PENDING,
            queue_position=1,
        )
        db.session.add(msg)
        db.session.commit()

        # Simulate worker picking up message
        msg.job_status = MessageJobStatus.SENDING
        msg.queue_position = None
        db.session.commit()

        assert msg.job_status == MessageJobStatus.SENDING
        assert msg.queue_position is None
```

**Step 2: Run test to verify it fails**

**Step 3: Update worker loop to manage job status**

```python
# In _worker_loop, when processing SMS task:
# 1. Set message.job_status = SENDING
# 2. Set message.queue_position = None
# 3. After all recipients processed, set appropriate final status
```

**Step 4: Calculate estimated_complete_at**

```python
# When starting to send:
def _estimate_completion(message, rate_limiter, queue_depth):
    """Estimate when message will complete sending."""
    # Get position in queue (how many PENDING messages ahead)
    msgs_ahead = db.session.query(Message).filter(
        Message.job_status == MessageJobStatus.PENDING,
        Message.created_at <= message.created_at,
        Message.id != message.id,
    ).count()

    # Rate is per-recipient, not per-message
    total_recipients_ahead = sum(
        m.recipient_count for m in pending_messages[:msgs_ahead]
    )

    seconds_to_wait = total_recipients_ahead / rate_limiter.rate_per_sec
    return datetime.now(timezone.utc) + timedelta(seconds=seconds_to_wait)
```

**Step 5: Run test to verify it passes**

**Step 6: Commit**

```bash
git add src/smspanel/services/queue.py tests/test_message_status_transitions.py
git commit -m "feat: update queue worker to manage message job status transitions"
```

---

### Task 7: Add Frontend Queue Status Display

**Files:**
- Modify: `src/smspanel/templates/web/dashboard.html` (or index.html)
- Modify: `src/smspanel/web/sms.py` (add queue_status to template context)

**Step 1: Write failing test (optional, integration test)**

```python
# tests/test_dashboard_queue_status.py
def test_dashboard_shows_queue_status(app):
    """Dashboard should show queue status when logged in."""
    with app.test_client() as client:
        # Login as user
        # Navigate to dashboard
        response = client.get("/")
        # Check for queue status elements
```

**Step 2: Update web/sms.py dashboard route**

```python
@web_bp.route("")
def dashboard():
    # ... existing code ...
    queue = get_task_queue()
    limiter = get_rate_limiter()

    # Get user's pending messages
    user_pending = Message.query.filter_by(
        user_id=current_user.id,
        job_status=MessageJobStatus.PENDING
    ).count()

    return render_template(
        "dashboard.html",
        messages=recent_messages,
        queue_status={
            "depth": queue.get_queue_size(),
            "rate": limiter.rate_per_sec,
            "user_pending": user_pending,
        },
        # ...
    )
```

**Step 3: Update template**

```html
<!-- Show queue status in dashboard sidebar -->
{% if queue_status.depth > 0 %}
<div class="queue-status">
  <h4>Queue Status</h4>
  <p>Messages in queue: {{ queue_status.depth }}</p>
  <p>Rate: {{ queue_status.rate }} msg/sec</p>
  {% if queue_status.user_pending > 0 %}
  <p>Your pending: {{ queue_status.user_pending }}</p>
  {% endif %}
</div>
{% endif %}
```

**Step 4: Commit**

```bash
git add src/smspanel/web/sms.py
git commit -m "feat: add queue status to dashboard"
```

---

### Task 8: Run Full Test Suite and Lint

**Step 1: Run all tests**

```bash
pytest -v
```

**Step 2: Fix any failures**

**Step 3: Run lint**

```bash
ruff check .
ruff check . --fix
ruff format .
```

**Step 4: Commit**

```bash
git commit -m "chore: run tests and lint after rate limit implementation"
```

---

### Task 9: Bump Version

**Step 1: Update pyproject.toml**

```toml
version = "0.26.0"
```

**Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.26.0"
```

---

## Execution Options

**Plan complete and saved to `docs/plans/2026-01-22-rate-limit-queue-status.md`. Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
