# Rename Project: ccdemo to smspanel

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename the entire Python project from "ccdemo" to "smspanel" across all configuration files, imports, directory names, and documentation.

**Architecture:** This is a project-wide renaming task that involves:
1. Renaming the main Python package directory
2. Updating all import statements across the codebase
3. Updating project metadata in configuration files
4. Updating documentation
5. Cleaning up auto-generated artifacts

**Tech Stack:** Python 3.12+, Flask, SQLAlchemy, pytest

---

## Overview

The project "ccdemo" needs to be renamed to "smspanel" to better reflect its purpose as an SMS management panel. This involves:

- **Directory rename**: `src/ccdemo/` → `src/smspanel/`
- **Import updates**: All `from ccdemo import ...` → `from smspanel import ...`
- **Mock patch paths**: All `@patch("ccdemo...")` → `@patch("smspanel...")`
- **Package metadata**: `pyproject.toml` name field
- **Documentation**: README.md references
- **Build artifacts**: Remove and regenerate `.egg-info`

---

### Task 1: Create backup commit

**Purpose:** Create a safety checkpoint before making structural changes.

**Step 1: Create commit**

```bash
git add -A
git commit -m "backup: state before project rename to smspanel"
```

---

### Task 2: Update Python package name in pyproject.toml

**Files:**
- Modify: `pyproject.toml:2`

**Step 1: Update project name**

```toml
name = "smspanel"
```

**Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "refactor: update project name to smspanel in pyproject.toml"
```

---

### Task 3: Update imports in src/__init__.py

**Files:**
- Modify: `src/__init__.py`

**Step 1: Update docstring**

```python
"""smspanel package."""
```

**Step 2: Commit**

```bash
git add src/__init__.py
git commit -m "refactor: update package docstring to smspanel"
```

---

### Task 4: Update imports in src/ccdemo/__init__.py

**Files:**
- Modify: `src/ccdemo/__init__.py`

**Step 1: Update docstring**

```python
"""smspanel application factory."""
```

**Step 2: Commit**

```bash
git add src/ccdemo/__init__.py
git commit -m "refactor: update app docstring to smspanel"
```

---

### Task 5: Update imports in run.py

**Files:**
- Modify: `run.py:3`

**Step 1: Update import statement**

```python
from smspanel import create_app
```

**Step 2: Commit**

```bash
git add run.py
git commit -m "refactor: update import in run.py to smspanel"
```

---

### Task 6: Update imports in init_db.py

**Files:**
- Modify: `init_db.py:4`

**Step 1: Update import statement**

```python
from smspanel import create_app, db
```

**Step 2: Commit**

```bash
git add init_db.py
git commit -m "refactor: update imports in init_db.py to smspanel"
```

---

### Task 7: Update imports in tests/conftest.py

**Files:**
- Modify: `tests/conftest.py:5-6`

**Step 1: Update import statements**

```python
from smspanel import create_app, db
from smspanel.models import User, Message, Recipient
```

**Step 2: Commit**

```bash
git add tests/conftest.py
git commit -m "refactor: update imports in conftest.py to smspanel"
```

---

### Task 8: Update imports in tests/test_api.py

**Files:**
- Modify: `tests/test_api.py:3-4`

**Step 1: Update import statements**

```python
from smspanel import db
from smspanel.models import Message, Recipient
```

**Step 2: Commit**

```bash
git add tests/test_api.py
git commit -m "refactor: update imports in test_api.py to smspanel"
```

---

### Task 9: Update mock patch paths in tests/test_hkt_sms.py

**Files:**
- Modify: `tests/test_hkt_sms.py`

**Step 1: Update patch path in send_sms test (line ~37)**

```python
@patch("smspanel.services.hkt_sms.requests.post")
```

**Step 2: Update patch path in send_single_recipient test (line ~54)**

```python
@patch("smspanel.services.hkt_sms.requests.post")
```

**Step 3: Update patch path in send_multiple_recipients test (line ~66)**

```python
@patch("smspanel.services.hkt_sms.requests.post")
```

**Step 4: Update patch path in handle_error_response test (line ~77)**

```python
@patch("smspanel.services.hkt_sms.requests.post")
```

**Step 5: Update patch path in handle_timeout test (line ~94)**

```python
@patch("smspanel.services.hkt_sms.requests.post")
```

**Step 6: Update patch path in queue_enqueue_test test (line ~124)**

```python
@patch("smspanel.services.hkt_sms.requests.post")
```

**Step 7: Commit**

```bash
git add tests/test_hkt_sms.py
git commit -m "refactor: update mock patch paths to smspanel"
```

---

### Task 10: Update import statement in tests/test_hkt_sms.py

**Files:**
- Modify: `tests/test_hkt_sms.py:5`

**Step 1: Update import**

```python
from smspanel.services.hkt_sms import HKTSMSService
```

**Step 2: Commit**

```bash
git add tests/test_hkt_sms.py
git commit -m "refactor: update service import to smspanel"
```

---

### Task 11: Remove old build artifacts

**Purpose:** Remove `.egg-info` directory which contains references to old package name.

**Step 1: Remove egg-info directory**

```bash
rm -rf src/ccdemo.egg-info
```

**Step 2: Commit**

```bash
git add src/ccdemo.egg-info
git commit -m "chore: remove old build artifacts"
```

---

### Task 12: Rename main package directory

**Purpose:** Rename the Python package directory from `ccdemo` to `smspanel`.

**Step 1: Rename directory**

```bash
cd /Users/gordon/Documents/repos/ccdemo
git mv src/ccdemo src/smspanel
```

**Step 2: Commit**

```bash
git add -A
git commit -m "refactor: rename package directory from ccdemo to smspanel"
```

---

### Task 13: Update README.md title

**Files:**
- Modify: `README.md:1`

**Step 1: Update title**

```markdown
# smspanel
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README title to smspanel"
```

---

### Task 14: Update README.md deployment references

**Files:**
- Modify: `README.md:133` - directory name
- Modify: `README.md:202` - systemd service name
- Modify: `README.md:212` - working directory
- Modify: `README.md:213` - PATH environment
- Modify: `README.md:214` - ExecStart path
- Modify: `README.md:223-225` - systemctl commands
- Modify: `README.md:264` - backup cron path
- Modify: `README.md:308` - project structure

**Step 1: Update directory name in cd command (line ~133)**

```bash
cd smspanel
```

**Step 2: Update systemd service name (line ~202)**

```ini
Create `/etc/systemd/system/smspanel.service`:
```

**Step 3: Update working directory (line ~212)**

```ini
WorkingDirectory=/path/to/smspanel
```

**Step 4: Update PATH environment (line ~213)**

```ini
Environment="PATH=/path/to/smspanel/.venv/bin"
```

**Step 5: Update ExecStart path (line ~214)**

```ini
ExecStart=/path/to/smspanel/.venv/bin/gunicorn -w 4 -b 0.0.0.0:3570 run:app
```

**Step 6: Update systemctl commands (lines ~223-225)**

```bash
sudo systemctl enable smspanel
sudo systemctl start smspanel
sudo systemctl status smspanel
```

**Step 7: Update backup cron path (line ~264)**

```bash
0 2 * * * cp /path/to/smspanel/instance/sms.db /backups/sms_$(date +\%Y\%m\%d).db
```

**Step 8: Update project structure (line ~308)**

```markdown
smspanel/
│   └── smspanel/
```

**Step 9: Commit**

```bash
git add README.md
git commit -m "docs: update all README.md references to smspanel"
```

---

### Task 15: Update CLAUDE.md project references

**Files:**
- Modify: `CLAUDE.md` - Check for any ccdemo references

**Step 1: Search and review ccdemo references**

```bash
grep -n "ccdemo" /Users/gordon/Documents/repos/ccdemo/CLAUDE.md
```

**Step 2: Update any found references (if any exist)**

Replace all occurrences of `ccdemo` with `smspanel`.

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md references to smspanel"
```

---

### Task 16: Update configuration reference in README.md

**Files:**
- Modify: `README.md:348`

**Step 1: Update config path reference**

```markdown
Configuration is in `src/smspanel/config.py`. The following environment variables are required:
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update config path in README to smspanel"
```

---

### Task 17: Reinstall package in editable mode

**Purpose:** Ensure the renamed package installs correctly.

**Step 1: Uninstall old package**

```bash
pip uninstall -y ccdemo
```

**Step 2: Install new package**

```bash
pip install -e .
```

**Step 3: Verify installation**

```bash
pip show smspanel
```

Expected: Output showing `Name: smspanel` with correct version and location.

---

### Task 18: Run tests to verify changes

**Purpose:** Ensure all imports work correctly after renaming.

**Step 1: Run all tests**

```bash
pytest -v
```

Expected: All tests pass without import errors.

**Step 2: Run with coverage**

```bash
pytest --cov=src/smspanel --cov-report=term-missing
```

Expected: Coverage report generates successfully.

---

### Task 19: Verify application starts

**Purpose:** Ensure the Flask application can start with the new package name.

**Step 1: Start application**

```bash
python run.py &
```

**Step 2: Wait and check process**

```bash
sleep 3
ps aux | grep "python run.py" | grep -v grep
```

Expected: Process is running.

**Step 3: Stop application**

```bash
pkill -f "python run.py"
```

**Step 4: Commit final verification (no files to add, just closing)**

---

### Task 20: Final cleanup - remove venv references (optional)

**Purpose:** Update virtual environment metadata to reflect new project name.

**Step 1: Update pyvenv.cfg (optional)**

```bash
sed -i '' 's/ccdemo/smspanel/g' .venv/pyvenv.cfg
```

**Note:** This file is auto-generated and will be recreated if venv is recreated. Skipping this step is acceptable.

---

## Summary of Changes

After completing all tasks:

1. Package renamed: `ccdemo` → `smspanel`
2. Directory renamed: `src/ccdemo/` → `src/smspanel/`
3. All imports updated across source and test files
4. Mock patch paths updated in tests
5. Documentation updated (README.md)
6. Build artifacts cleaned and regenerated
7. Package reinstalled successfully

---

## Rollback Plan

If anything goes wrong, revert to the backup commit:

```bash
git reflog  # Find the backup commit hash
git reset --hard <backup-commit-hash>
pip uninstall -y smspanel
pip install -e .
```
