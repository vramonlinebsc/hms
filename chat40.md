Understood. Here is a **clean, factual, copy-pasteable summary** for starting a **new chat**, with no speculation and no instructions mixed in.

---

# 🔒 HMS — **CI vs Local Pytest Mismatch (AUTHORITATIVE SUMMARY)**

## ✅ What is Correct and Proven

### Local Environment

* `pytest -q` **passes locally** (4 tests, only datetime warnings).
* Backend logic is correct.
* Tests are correct.
* `backend/routes.py` **does NOT** define:

  * `/patient/register`
  * `/patient/login`
* Patient auth routes exist **only** in `backend/routes_patient.py`.
* `backend/app.py` correctly registers:

  * `health_bp`
  * `auth_bp`
  * `patient_bp`
  * `doctor_bp`
  * `admin_bp`
* `git ls-files` confirms:

  * `backend/routes_patient.py` is tracked
  * correct casing
  * file exists in repo
* `git status` shows:

  * `routes.py` and `routes_patient.py` are clean
  * no uncommitted changes to routing files

---

## ❌ What is Failing (CI Only)

GitHub Actions consistently reports:

* `/patient/register` → **404 NOT FOUND**
* `/patient/login` → response JSON is `None`
* Tests fail with:

  * `TypeError: 'NoneType' object is not subscriptable`
  * `assert 404 == 201`

This failure signature **exactly matches an old routing layout** where:

* `/patient/login` existed under `auth_bp`
* `/patient/register` did not exist

---

## 🔍 Critical Evidence from CI

### CI Flask URL Map (Captured Explicitly)

CI shows routes such as:

* `/patient/login -> auth.patient_login`
* **NO** `/patient/register`

This directly contradicts the current `routes.py` and `routes_patient.py` in the repository.

---

## 🚨 Key Contradiction

* Local code + local pytest: **correct**
* Git-tracked files: **correct**
* CI runtime behavior: **matches an older commit**

This means:

> **GitHub Actions is not executing the same routing tree that exists in the repository HEAD**, despite multiple pushes, empty commits, and forced reruns.

---

## ❌ What Is Ruled Out

* Flask bug
* Pytest bug
* Blueprint registration bug
* Windows vs Linux case sensitivity
* Missing commits
* `.gitignore`
* Cached workflow YAML
* Wrong test fixture
* Wrong app factory
* Wrong DB setup

All of these were explicitly checked and disproven.

---

## 📌 Current State

| Area            | Status                            |
| --------------- | --------------------------------- |
| Backend logic   | ✅ Correct                         |
| Tests           | ✅ Correct                         |
| Local pytest    | ✅ Passing                         |
| Repo file state | ✅ Correct                         |
| CI execution    | ❌ Running stale routing           |
| Root cause      | ❓ CI checkout / execution anomaly |

---

## 🎯 Reason for New Chat

At this point:

* Further debugging inside the same thread is counter-productive.
* A fresh chat is needed to:

  * re-establish context cleanly
  * re-inspect CI execution assumptions
  * possibly simplify CI invocation to a minimal reproducer

---

## ▶️ Instruction for New Chat

Paste this summary and say:

> **“Local pytest passes, CI runs an older routing tree. Let’s isolate CI execution to a minimal reproducer.”**

This is the exact, correct restart point.

