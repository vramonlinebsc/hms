
# 🏥 Hospital Management System – Backend

A **production-oriented backend system** for managing clinic and hospital operations, built with **Flask** and **SQLite**, and designed using real-world SaaS engineering practices.

This project focuses on **correct domain modeling, security, and operational control**, not UI demos or tutorial shortcuts.

---

## ✨ Key Features

### 🔐 Authentication & Authorization
- JWT-based authentication
- Strict role-based access control:
  - **Admin**
  - **Doctor**
  - **Patient**
- Token expiry enforcement
- Request-scoped identity and role validation

---

### 📅 Appointment Management
- Secure appointment booking with **doctor-level conflict prevention**
- Full appointment lifecycle:


BOOKED → COMPLETED | CANCELLED | NO_SHOW

- Patient-initiated cancellations
- Doctor-completed consultations with diagnosis and treatment notes
- Admin-triggered NO_SHOW automation

---

### 👁️ Role-Based Views
- **Admin**
- Global appointment visibility
- Filter by status, doctor, and date
- Doctor blacklisting / unblacklisting
- **Doctor**
- Personal schedule view only
- Availability management
- **Patient**
- Complete appointment history
- Includes doctor details and medical notes

---

### ⚙️ Administration & Control
- Programmatically seeded admin user
- Doctor blacklisting enforced at login level
- Idempotent admin automation actions
- No business logic leakage into auth decorators

---

## 🧠 Design Highlights

- **Programmatic database initialization** (`init_db.py`) as the single source of truth
- Deterministic schema creation (no manual DB setup)
- Clean separation of concerns (auth, domain logic, admin control)
- Safe read/write API boundaries
- Automation-ready architecture (background jobs can be added without refactor)
- All APIs verified end-to-end using REST clients (`curl`)

> This repository intentionally avoids UI code to keep backend architecture and correctness the primary focus.

---

## 🧭 SaaS Maturity Classification

**Early Production-Grade SaaS Backend (Strong MVP+)**

This system goes well beyond academic CRUD projects and bootcamp demos and aligns with **real SaaS and internal enterprise backend standards**.

**What this represents:**
- Correct lifecycle modeling for healthcare workflows
- Explicit operational authority and observability
- Security-first API boundaries
- Automation treated as a first-class concern
- Engineering discipline suitable for real-world pilots

**Suitable for:**
- Recruiter and senior-engineer review
- Internal hospital or clinic tools
- Early-stage healthtech SaaS MVPs

**Intentionally deferred:**
- Background workers (Celery / Redis)
- Audit logs and metrics
- Email and notification pipelines
- Frontend (Vue / React Native planned separately)

---

## 🧩 Technology Stack

- **Backend Framework**: Flask
- **Database**: SQLite
- **Authentication**: JWT
- **Language**: Python 3

---

## 📌 Positioning Note

This project is designed as a **real-world backend foundation**, not a toy app or tutorial exercise.

When describing it:
> “A production-oriented clinic backend with role-based access control and complete appointment lifecycle modeling.”

That description is accurate and intentional.

---
