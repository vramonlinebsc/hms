Below is a **clean, authoritative summary** you can paste into a **new chat** to continue without losing context.

---

# 🔒 HMS — **BACKEND TESTING & STATUS SUMMARY (FOR NEXT CHAT)**

## 🎯 Project Context

**Hospital Management System (HMS)** for **MAD2**, with:

* Flask backend (application factory)
* SQLite database
* JWT auth with strict role enforcement
* Deterministic appointment lifecycle
* Admin / Doctor / Patient roles
* Backend-first, frontend later

Backend logic for **HMS-2 (Admin)**, **HMS-3 (Doctor)**, **HMS-4 (Patient)** has been implemented and iteratively corrected.

---

## 🧪 Pytest Integration — What Was Done

### Test Infrastructure

* `pytest` installed in venv
* `pytest.ini` added:

  ```ini
  [pytest]
  pythonpath = .
  testpaths = backend/tests
  ```
* `backend/__init__.py` added so `backend.*` imports work
* SMTP debug file renamed to avoid pytest discovery
* Tests structured as black-box API tests using Flask test client

Test files involved:

* `test_auth.py`
* `test_patient_appointments.py`
* `test_admin_appointments.py`

---

## ✅ What Is Working (Confirmed by Tests)

### Admin

* Admin login works
* Admin can list appointments
* Admin can cancel appointments
* Admin audit logging fixed to include:

  * `actor_role`
  * `actor_id`

### Patient

* Patient login works
* Patient can book appointments (when no conflict)
* Patient lifecycle guards (time checks, ownership) are enforced

---

## ❌ Current Failing Issues (ROOT CAUSES IDENTIFIED)

### 1️⃣ **Patient Registration Test Failure**

**Symptom**

```
test_patient_register_and_login → 400 instead of 201
```

**Cause**

* Tests share the same SQLite DB across test cases
* Same usernames reused across tests
* Backend correctly rejects duplicate usernames

**Conclusion**

* Backend behavior is correct
* Tests must use **globally unique usernames** or DB isolation

---

### 2️⃣ **Patient Cancellation Integrity Error**

**Symptom**

```
sqlite3.IntegrityError: CHECK constraint failed: status IN (...)
```

**Cause**

* DB schema `appointments.status` CHECK constraint allows only:

  ```
  BOOKED
  COMPLETED
  CANCELLED_BY_ADMIN
  NO_SHOW
  ```
* Backend logic uses:

  ```
  CANCELLED_BY_PATIENT
  ```
* Schema and code are **out of sync**

**Conclusion**

* This is a **real schema bug**, not a test issue
* Options (to decide next chat):

  1. Extend DB CHECK constraint to include `CANCELLED_BY_PATIENT`
  2. Align backend to existing schema (less correct semantically)

---

### 3️⃣ **Test DB Isolation Is Missing**

**Observed Effects**

* Appointment overlap conflicts across tests
* Registration collisions
* State leakage between tests

**Underlying Cause**

* `get_db()` uses a fixed SQLite DB (`hms.db`)
* Tests do NOT get a fresh database per test/session

**Conclusion**

* Need **one of the following** next:

  * Make DB path configurable via env var (preferred)
  * Or recreate schema per test session

---

## 📌 Key Insight (Very Important)

At this point:

* **Backend logic is mostly correct**
* **Tests are doing their job** by exposing:

  * Schema–logic mismatches
  * Missing test isolation

This is no longer “writing tests”, but **deciding final backend contracts**.

---

## 🔐 Current State

| Area                | Status                                  |
| ------------------- | --------------------------------------- |
| HMS-2 Admin logic   | Implemented, tested                     |
| HMS-3 Doctor logic  | Implemented                             |
| HMS-4 Patient logic | Implemented                             |
| Backend logic       | Mostly stable                           |
| DB schema           | ❌ Not aligned with patient cancellation |
| Pytest setup        | Working                                 |
| Tests               | Failing for valid structural reasons    |

---

## ▶️ Instruction for Next Chat

Paste this summary and say:

> **“Let’s finish backend testing by fixing DB schema vs lifecycle and test isolation.”**

This will resume exactly at the right decision point:

* whether to change schema
* how to isolate DB for tests
* then freeze backend permanently before frontend work

