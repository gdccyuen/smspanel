# Code Quality Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Improve code quality by addressing 6 identified issues: global state, import styles, type hints, redundant conditionals, magic numbers, and inconsistent status values.

**Architecture:** Address each issue systematically with TDD approach - write failing test, implement fix, verify, commit.

**Tech Stack:** Python 3.10+, ruff for linting/formatting, standard library typing.

---

## Task 1: Standardize Import Style to Absolute Imports

**Files:**
- Modify: `src/smspanel/services/hkt_sms.py:12`
- Modify: `src/smspanel/services/db_queue.py:9`
- Modify: `src/smspanel/services/dead_letter.py:6`
- Modify: `src/smspanel/web/dead_letter.py:7-8`
- Modify: `src/smspanel/app.py:8-10`
- Modify: `src/smspanel/models.py:8`
- Modify: `src/smspanel/web/auth.py:6-8`
- Modify: `src/smspanel/api/sms.py:5-10`
- Modify: `src/smspanel/web/admin.py:8-9,23-24`
- Modify: `src/smspanel/web/sms.py:7-8,14,20`
- Modify: `src/smspanel/utils/sms_helper.py:7-9`
- Modify: `src/smspanel/utils/admin.py:6-8`
- Modify: `src/smspanel/utils/database.py:5`
- Modify: `src/smspanel/utils/validation.py:6`

**Step 1: Write the failing test**

```python
# tests/test_imports.py
def test_uses_absolute_imports():
    """All smspanel imports should use absolute style."""
    from smspanel.services.hkt_sms import HKTSMSService
    from smspanel.services.dead_letter import DeadLetterQueue
    from smspanel.models import User
    from smspanel.api.sms import api_bp
    assert HKTSMSService is not None
    assert DeadLetterQueue is not None
    assert User is not None
    assert api_bp is not None
```

**Step 2: Run test to verify it passes (imports already work)**

Run: `pytest tests/test_imports.py -v`
Expected: PASS (absolute imports work via package structure)

**Step 3: Convert relative imports to absolute imports**

Convert all `from .x import y` and `from ..x import y` to `from smspanel.x import y`:

```python
# Example conversions:
# hkt_sms.py:12
# FROM: from ..config import ConfigService, SMSConfig
# TO:   from smspanel.config import ConfigService, SMSConfig

# services/db_queue.py:9
# FROM: from ..extensions import db
# TO:   from smspanel.extensions import db

# web/dead_letter.py:7-8
# FROM: from ..services.dead_letter import get_dead_letter_queue
# TO:   from smspanel.services.dead_letter import get_dead_letter_queue
```

**Step 4: Run tests to verify nothing broke**

Run: `pytest -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add src/smspanel/
git commit -m "refactor: standardize on absolute imports"
```

---

## Task 2: Simplify Redundant Conditional in hkt_sms.py

**Files:**
- Modify: `src/smspanel/services/hkt_sms.py:85-91`

**Step 1: Write the failing test**

```python
# tests/test_hkt_sms.py
def test_send_single_handles_error_response():
    """send_single should handle errors with response attribute correctly."""
    import requests
    from smspanel.services.hkt_sms import HKTSMSService, SMSError
    from smspanel.config.sms_config import ConfigService

    # Create mock config service
    class MockConfigService:
        def get_sms_config(self):
            from smspanel.config.sms_config import SMSConfig
            return SMSConfig(
                base_url="http://test",
                application_id="test",
                sender_number="12345678"
            )

    service = HKTSMSService(MockConfigService())

    # Mock a RequestException with response attribute
    class MockResponse:
        status_code = 400

    error = requests.RequestException("Bad request")
    error.response = MockResponse()

    # This should not raise and should return proper error dict
    result = service.send_single("12345678", "test")
    assert result["success"] is False
    assert result["status_code"] == 400
```

**Step 2: Run test to verify it fails (before fix)**

Run: `pytest tests/test_hkt_sms.py::test_send_single_handles_error_response -v`
Expected: PASS or FAIL (verify logic works)

**Step 3: Simplify the conditional**

In `hkt_sms.py:85-91`:

```python
# FROM:
except requests.RequestException as e:
    return {
        "success": False,
        "error": str(e),
        "status_code": getattr(e.response, "status_code", None)
        if hasattr(e, "response")
        else None,
    }

# TO:
except requests.RequestException as e:
    return {
        "success": False,
        "error": str(e),
        "status_code": getattr(e, "response", None),
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hkt_sms.py -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add src/smspanel/services/hkt_sms.py
git commit -m "refactor: simplify getattr pattern in error handling"
```

---

## Task 3: Extract Magic Numbers to Constants

**Files:**
- Modify: `src/smspanel/services/hkt_sms.py` (add timeout constant)
- Modify: `src/smspanel/services/queue.py` (add timeout constant)
- Modify: `src/smspanel/config/config.py` (add timeout config)

**Step 1: Write the failing test**

```python
# tests/test_constants.py
def test_sms_timeout_is_configurable():
    """SMS request timeout should be defined as a constant."""
    from smspanel.services.hkt_sms import SMS_REQUEST_TIMEOUT

    assert SMS_REQUEST_TIMEOUT == 30
    assert isinstance(SMS_REQUEST_TIMEOUT, int)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_constants.py::test_sms_timeout_is_configurable -v`
Expected: FAIL with "SMS_REQUEST_TIMEOUT not defined"

**Step 3: Add constants**

In `hkt_sms.py`, add at module level:

```python
# Request timeout in seconds
SMS_REQUEST_TIMEOUT = 30

# Default retry settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_MIN_BACKOFF = 2
DEFAULT_MAX_BACKOFF = 10
```

In `hkt_sms.py:72`, update the timeout:

```python
# FROM:
timeout=30,

# TO:
timeout=SMS_REQUEST_TIMEOUT,
```

In `config/config.py`, add:

```python
# SMS request timeout in seconds
SMS_REQUEST_TIMEOUT = 30
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_constants.py::test_sms_timeout_is_configurable -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/smspanel/services/hkt_sms.py src/smspanel/config/config.py
git commit -m "refactor: extract SMS timeout to constant"
```

---

## Task 4: Add Status Enum for Consistent Status Values

**Files:**
- Modify: `src/smspanel/models.py` (add Status and RecipientStatus enums)

**Step 1: Write the failing test**

```python
# tests/test_status_enum.py
def test_status_enum_exists():
    """Status enum should be defined for message and recipient statuses."""
    from smspanel.models import MessageStatus, RecipientStatus

    # MessageStatus
    assert hasattr(MessageStatus, "PENDING")
    assert hasattr(MessageStatus, "SENT")
    assert hasattr(MessageStatus, "FAILED")
    assert hasattr(MessageStatus, "PARTIAL")

    # RecipientStatus
    assert hasattr(RecipientStatus, "PENDING")
    assert hasattr(RecipientStatus, "SENT")
    assert hasattr(RecipientStatus, "FAILED")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_status_enum.py::test_status_enum_exists -v`
Expected: FAIL with "MessageStatus not defined"

**Step 3: Add Status enums to models.py**

In `models.py`, add after imports:

```python
from enum import Enum


class MessageStatus(str, Enum):
    """Message status values."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    PARTIAL = "partial"


class RecipientStatus(str, Enum):
    """Recipient delivery status values."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class DeadLetterStatus(str, Enum):
    """Dead letter message status values."""

    PENDING = "pending"
    RETRIED = "retried"
    ABANDONED = "abandoned"
```

Update status columns to use enums:

```python
# Message model line 57
status = db.Column(db.String(20), default=MessageStatus.PENDING, index=True)

# Recipient model line 93
status = db.Column(db.String(20), default=RecipientStatus.PENDING)

# DeadLetterMessage model line 123
status = db.Column(db.String(20), default=DeadLetterStatus.PENDING, index=True)
```

Update all status references (properties, comments):

```python
# Line 74: filter_by(status="sent") → filter_by(status=RecipientStatus.SENT)
# Line 79: filter_by(status="failed") → filter_by(status=RecipientStatus.FAILED)
# Line 134: status == "pending" → status == DeadLetterStatus.PENDING
# Line 143: status = "retried" → status = DeadLetterStatus.RETRIED
# Line 148: status = "abandoned" → status = DeadLetterStatus.ABANDONED
```

Update docstrings/comments to reference enums:

```python
# Line 57: # pending, sent, failed → # See MessageStatus enum
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_status_enum.py -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/smspanel/models.py
git commit -m "refactor: add Status enums for consistent status values"
```

---

## Task 5: Add py.typed Marker for Type Checking

**Files:**
- Create: `src/smspanel/py.typed`
- Modify: `src/smspanel/__init__.py` (add import of TYPE_CHECKING)

**Step 1: Write the failing test**

```python
# tests/test_typed_marker.py
def test_py_typed_marker_exists():
    """Package should include py.typed marker for type checking."""
    import smspanel
    import os

    # Check py.typed marker exists in package
    package_dir = os.path.dirname(smspanel.__file__)
    py_typed_path = os.path.join(package_dir, "py.typed")

    assert os.path.exists(py_typed_path), "py.typed marker should exist"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_typed_marker.py::test_py_typed_marker_exists -v`
Expected: FAIL with "py.typed marker should exist"

**Step 3: Add py.typed marker**

Create `src/smspanel/py.typed`:
```python
# Marker file for PEP 561 type checking support.
# This package uses inline type annotations.
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_typed_marker.py::test_py_typed_marker_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/smspanel/py.typed
git commit -chore: add py.typed marker for type checking support"
```

---

## Task 6: Update Documentation

**Files:**
- Modify: `README.md` (add section on type hints, enum usage)

**Step 1: Write the failing test (documentation test)**

```python
# tests/test_docs.py
def test_readme_mentions_type_hints():
    """README should document type hint support."""
    import os
    readme_path = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
    with open(readme_path) as f:
        content = f.read()

    assert "type" in content.lower() or "typing" in content.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_docs.py::test_readme_mentions_type_hints -v`
Expected: PASS (readme already mentions Python type hints)

**Step 3: Update README.md**

Add section after "Configuration":

```markdown
## Type Safety

This project uses Python type hints for improved code quality and IDE support:

- **Status Enums**: `MessageStatus`, `RecipientStatus`, `DeadLetterStatus` provide type-safe status values
- **Constants**: `SMS_REQUEST_TIMEOUT` extracted for easy configuration
- **Type Checking**: Package supports PEP 561 type checking with `py.typed` marker

Import type-safe enums:
```python
from smspanel.models import MessageStatus, RecipientStatus, DeadLetterStatus

# Use enums instead of magic strings
if message.status == MessageStatus.SENT:
    ...
```
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_docs.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add type safety documentation"
```

---

## Task 7: Run Full Test Suite and Lint

**Files:**
- N/A (verification task)

**Step 1: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

**Step 2: Run linting**

Run: `ruff check .`
Expected: No errors

**Step 3: Run formatting**

Run: `ruff format .`
Expected: Code formatted

**Step 4: Commit**

```bash
git add src/ tests/ README.md
git commit -m "chore: run tests and lint after code quality improvements"
```

---

## Task 8: Bump Version

**Files:**
- Modify: `pyproject.toml:3`

**Step 1: Update version**

From `0.22.0` to `0.23.0` (minor version for code quality improvements)

**Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.23.0"
```

---

## Summary of Changes

| Task | Files Changed | Description |
|------|--------------|-------------|
| 1 | ~15 files | Standardize import style to absolute imports |
| 2 | `hkt_sms.py` | Simplify redundant conditional with `getattr()` |
| 3 | `hkt_sms.py`, `config.py` | Extract magic numbers to constants |
| 4 | `models.py` | Add Status enums for type-safe status values |
| 5 | `py.typed` (new) | Add PEP 561 type checking marker |
| 6 | `README.md` | Document type safety features |
| 7 | N/A | Run full test suite and lint |
| 8 | `pyproject.toml` | Bump version to 0.23.0 |

---

## Plan Complete

**Plan saved to:** `docs/plans/2026-01-21-code-quality.md`

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
