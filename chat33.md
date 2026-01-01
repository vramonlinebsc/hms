Below is the **clean, authoritative, copy-pasteable summary** to seed a **new chat**.

No commentary. No next steps mixed in.

---

# 🔒 HMS — **BACKEND HARDENING & LIFECYCLE (LOCKED SUMMARY)**

## 🎯 Scope of This Phase

Objective was to **stabilize backend lifecycle correctness** and eliminate subtle production risks by enforcing:

* Single source of truth
* Deterministic startup
* Canonical Flask patterns
* Zero hidden side-effects
* One change at a time, fully locked

---

## 🧱 Database Layer — Authoritative State

### ✅ SQLite Path (LOCKED)

* **Single DB file**:

  ```
  backend/hms.db
  ```
* Path resolved via:

  ```python
  os.path.join(os.path.dirname(__file__), "hms.db")
  ```
* No CWD-dependent behavior possible.

---

### ✅ Connection Lifecycle (LOCKED)

* One SQLite connection **per request**
* Connection stored in Flask `g`
* Always closed via **canonical Flask teardown**

**`backend/db.py` (authoritative):**

```python
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```

* No signals
* No import-time side effects
* Flask-documented best practice

---

## 🧱 Application Startup — Deterministic

### ✅ `init_db()` Execution (LOCKED)

* `init_db()` runs **only once**
* Called only inside:

  ```python
  if __name__ == "__main__":
  ```
* Never executed at import time
* Safe under debug reloads and production WSGI

---

## 🧱 JWT Configuration — Single Source of Truth

* JWT secret, algorithm, expiry defined **only** in:

  ```
  backend/config.py
  ```
* Removed all duplicate config from `app.py`
* Login + verification guaranteed aligned

---

## 🧱 App Wiring — Final Canonical `app.py`

### ✅ Blueprint Registration (LOCKED)

* `health_bp`
* `auth_bp`
* `admin_bp`
* `metrics_bp`

All registered once, no duplication.

---

### ✅ DB Teardown Wiring (LOCKED)

* `init_app(app)` called exactly once inside `create_app()`
* Ensures DB cleanup for every request/app context

---

### ✅ Rate Limiting (LOCKED)

* Executed via `@app.before_request`
* Explicit behavior, no fake guards

```python
@app.before_request
def apply_rate_limit():
    limited = rate_limiter()
    if limited:
        return limited
    return None
```

* Deterministic
* Transparent
* Flask-correct

---

### ✅ Response Hardening (LOCKED)

* Audit headers injected on every response:

  * `X-Service`
  * `X-Version`
  * `X-Environment`

---

## 🔒 Final Invariants (Non-Negotiable)

* One DB file
* One DB connection per request
* Guaranteed teardown
* Deterministic startup
* No duplicated config
* No implicit behavior
* No speculative guards
* Production-grade Flask semantics

---

## ▶️ Instruction for New Chat

Paste **this entire summary** and say:

> **“Proceed with next HMS step.”**

This is the **only required context**.
