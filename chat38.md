Below is a **clean, authoritative, copy-pasteable summary** to seed the **next new chat**.
No commentary. No next steps mixed in.

---

# 🔒 HMS — **PROJECT CONTEXT & STATUS SUMMARY (FOR NEXT CHAT)**

## 🎯 Project Overview

**Hospital Management System (HMS)** built to satisfy the **MAD2 course requirements**, using the provided problem statement PDF as the **baseline authority** .

**Goal:**
Deliver a **locally runnable, role-based, end-to-end HMS** with deterministic backend behavior, usable UI, background jobs, and clear academic documentation.

---

## 🧱 Tech Stack (Locked by PDF)

* **Backend:** Flask (API-first)
* **Frontend:** Vue.js (Bootstrap only for styling)
* **Database:** SQLite (programmatically created)
* **Auth:** JWT-based role enforcement
* **Caching:** Redis (planned/partial)
* **Async Jobs:** Redis + Celery (planned)
* **Environment:** Local machine demo only (mandatory)

---

## 👥 Roles & Scope (PDF-Defined)

### Admin

* Pre-existing superuser (created programmatically)
* View KPIs (doctors, patients, appointments)
* View/manage all appointments
* Search doctors & patients
* Blacklist doctors (patient blacklist planned)

### Doctor

* Login & view assigned appointments
* Complete appointments (diagnosis, treatment)
* Cancel appointments (pre-start)
* Provide availability (7 days)
* View patient history (in progress)

### Patient

* Register & login
* Book/cancel appointments
* View appointment & treatment history
* Edit profile (planned)

*(Triage & Nurses acknowledged in PDF but not implemented — explicitly out of MVP scope.)*

---

## 🧱 Backend Status (Current)

* Flask app stable and runnable locally
* JWT auth with strict role checks
* Appointment lifecycle enforced:

  ```
  BOOKED → COMPLETED / CANCELLED / NO_SHOW
  ```
* Conflict prevention for overlapping appointments
* Canonical logic split into role-based blueprints
* Legacy routes removed / minimized
* Admin NO_SHOW & penalty logic implemented as **pure functions**
* Background jobs & caching not yet wired

---

## 📊 Jira Project Status (HMS Space)

### Epics (Created & Visible)

* **HMS-1:** Authentication & RBAC → **DONE**
* **HMS-2:** Admin Dashboard → **IN PROGRESS**
* **HMS-3:** Doctor Lifecycle → **IN PROGRESS**
* **HMS-4:** Patient Lifecycle → **IN PROGRESS**
* **HMS-5:** Appointment State Management → **DONE**
* **HMS-6:** Background Jobs → **TO DO**
* **HMS-7:** Performance Optimization → **TO DO**
* **HMS-8:** Academic Submission → **TO DO**

### Stories

* All stories **successfully created via Jira REST API**
* Correctly linked to epics (`HMS-1` … `HMS-8`)
* Creation confirmed by successful script execution:

  ```
  All stories created successfully.
  ```

*(CSV import via UI was blocked by Jira limitations; REST API used instead.)*

---

## 📄 Academic Alignment (PDF)

### Fully Implemented

* Role-based authentication
* Admin dashboard KPIs
* Appointment booking & lifecycle
* Doctor treatment updates
* Patient history viewing
* Conflict prevention
* Deterministic state transitions

### Partially Implemented / Pending

* Redis caching
* Celery background jobs:

  * Daily reminders
  * Monthly doctor report
  * CSV export (async)
* Search enhancements
* Profile editing
* Performance tuning

### Academic Deliverables (Pending)

* ER diagram
* API documentation
* Project report (≤5 pages)
* AI/LLM usage declaration
* Demo video (≤10 minutes)

---

## 🧠 Key Constraints (Non-Negotiable)

* SQLite only
* Bootstrap only (no other CSS frameworks)
* All DB creation via code (no manual DB tools)
* All demos must run locally
* Scope discipline: **MVP > extras**

---

## ▶️ Instruction for Next Chat

Paste **this entire summary** and say:

> **“Proceed with HMS coding — next focus: backend jobs and remaining Doctor/Patient lifecycle gaps.”**

This resumes work **with full project context loaded**.

