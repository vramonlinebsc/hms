
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


Good. **STEP 10 — README & Architecture Justification**
This is the **final, examiner-facing artifact**. No code. No new behavior.

Below is a **clean, copy-pasteable `README.md`** you can drop into the repo root.

---

# HMS — Hospital Management System (Backend)

## Overview

**HMS** is a **production-oriented hospital backend** built to demonstrate **backend engineering discipline**, not UI polish.

The system emphasizes:

* Determinism before features
* Idempotency over convenience
* Explicit lifecycle modeling
* Operational realism (async jobs, retries, guards)

This project is intentionally **backend-heavy** and **read-only UI-light**, aligned with MAD2 evaluation goals.

---

## Architecture Summary

### Technology Stack

| Layer | Choice               | Justification                      |
| ----- | -------------------- | ---------------------------------- |
| Web   | Flask                | Minimal, explicit, no magic        |
| DB    | SQLite               | Deterministic, portable, MAD2-safe |
| Auth  | JWT                  | Stateless, role-based              |
| Async | Celery + Redis       | Real background execution          |
| Email | smtplib (Gmail SMTP) | Zero framework coupling            |

---

## Why SQLite Is Acceptable

SQLite is used **by design**, not as a shortcut.

* Single-node backend (MAD2 scope)
* No concurrent write hotspots
* Deterministic schema creation
* Easy examiner verification
* Zero infra dependency

**All schema is created programmatically** via `init_db.py`, satisfying MAD2 rules.

If scaled:

* SQLite → PostgreSQL
* No schema or API redesign required

---

## Authentication & Authorization

* JWT-based authentication
* Roles enforced at decorator level
* No role mixing
* No implicit trust

Roles:

```
admin | doctor | patient
```

Every protected endpoint explicitly declares its role requirement.

---

## Appointment Lifecycle (Explicit State Machine)

Appointments follow a **strict lifecycle**:

```
BOOKED
 ├─→ COMPLETED   (doctor)
 ├─→ CANCELLED   (patient)
 └─→ NO_SHOW     (automation)
```

* No invalid transitions
* No silent state changes
* Every transition is traceable

This prevents:

* Double completion
* Retroactive edits
* Temporal inconsistencies

---

## Asynchronous Processing

### Why Celery Exists

Celery is used **only where async is necessary**:

* Email delivery
* Periodic automation (NO_SHOW detection)

Not used for:

* CRUD
* Business logic
* Reporting

This keeps async **controlled and auditable**.

---

## NO_SHOW Automation

A periodic job runs every 10 minutes:

1. Marks overdue appointments as `NO_SHOW`
2. Inserts penalties **idempotently**
3. Triggers email escalation **once**

Key properties:

* Safe to rerun
* Crash-resistant
* Retry-safe
* No duplicate emails

---

## Penalty & Escalation Design

Penalties are modeled explicitly:

* One row per NO_SHOW
* `UNIQUE(appointment_id)`
* `email_sent` guard

This ensures:

* Exactly-once email delivery
* Auditable history
* Future reversibility

---

## Metrics & Reporting (Read-Only)

Admin-only reporting endpoints provide:

* Total NO_SHOW count
* Penalties per patient
* NO_SHOWs per doctor

Design rules:

* Read-only
* SQL-driven
* Deterministic output
* Hard result caps

No dashboards, no mutations.

---

## Hardening Measures

Implemented deliberately, not cosmetically:

* Rate limiting (per IP, per endpoint)
* Pagination guards
* Audit response headers
* Config centralization
* Explicit app lifecycle

No Docker, OAuth, or infra noise — **by design**.

---

## What This Project Demonstrates

This backend shows:

* Real lifecycle modeling
* Correct async usage
* Idempotency discipline
* Examiner-defensible decisions
* Production thinking within academic scope

It is **not** a toy CRUD app.

---

## How This Would Scale (Conceptually)

Without rewriting:

* SQLite → PostgreSQL
* Redis → managed Redis
* Flask → Gunicorn + Nginx
* Single worker → horizontal workers

The **architecture already supports this**.

---

## Project Status

**All steps locked.**

* Core backend ✅
* Appointment lifecycle ✅
* Async infra ✅
* Automation & escalation ✅
* Metrics & hardening ✅
* Documentation complete ✅

---

### End of Project
Good. Then we **do this properly**, not as an afterthought.

I’ll be explicit, scoped, and **plan-first** so we don’t repeat the ambiguity you correctly called out.

---

# 🧭 HMS Frontend Program — MASTER PLAN

We will build **one world-class design system once**, then reuse it for:

* **Vue.js Web App** (now)
* **React Native Mobile Apps** (later)

This means:

* No UI throwaway
* No “exam demo” UI
* No framework-locked design decisions

---

## 0️⃣ Non-Negotiable Principles (LOCK THESE)

1. **Backend remains the source of truth**
2. **Frontend is stateless**
3. **API-driven UI only**
4. **Role-based UX (admin / doctor / patient)**
5. **Design tokens first, components second**
6. **Accessibility & performance by default**

---

## 1️⃣ Target UX Standard (What “World-Class” Means)

We are targeting:

* Clean, calm, clinical (not flashy)
* Fast first paint
* Zero cognitive overload
* Predictable navigation
* Mobile-first layouts

Think:

* NHS / Kaiser Permanente clarity
* Stripe / Linear interaction quality
* Apple-level restraint

---

## 2️⃣ High-Level Frontend Architecture

### Web (NOW)

```
hms-web/
├─ src/
│  ├─ api/              # API client (axios)
│  ├─ auth/             # token, role, guards
│  ├─ design-system/    # tokens, colors, spacing
│  ├─ components/       # reusable UI blocks
│  ├─ layouts/          # page shells
│  ├─ pages/            # route-level pages
│  ├─ router/           # vue-router
│  ├─ stores/           # Pinia state
│  └─ main.ts
```

### Mobile (LATER – planned now)

```
hms-mobile/
├─ src/
│  ├─ api/              # shared API schema
│  ├─ design-tokens/    # shared tokens (JSON)
│  ├─ screens/
│  ├─ components/
│  └─ navigation/
```

➡️ **Design tokens will be framework-agnostic JSON**
Vue + React Native both consume them.

---

## 3️⃣ Technology Choices (Justified)

### Web

| Area      | Choice           | Why                               |
| --------- | ---------------- | --------------------------------- |
| Framework | **Vue 3**        | Composition API, clean reactivity |
| Build     | **Vite**         | Fast, modern                      |
| State     | **Pinia**        | Explicit, testable                |
| Routing   | **vue-router**   | Mature                            |
| HTTP      | **Axios**        | Interceptors                      |
| Styling   | **Tailwind CSS** | Design tokens, consistency        |
| Forms     | **Native + Zod** | Predictable validation            |

### Mobile (Planned)

| Area       | Choice              |
| ---------- | ------------------- |
| Framework  | React Native        |
| Navigation | React Navigation    |
| Styling    | Token-driven        |
| API        | Same OpenAPI schema |

---

## 4️⃣ UX by Role (VERY IMPORTANT)

### Admin

* Metrics dashboard
* Penalty views
* Read-only analytics
* Calm, dense, professional

### Doctor

* Today’s appointments
* Complete appointment
* Availability management
* Fast, low friction

### Patient

* Book appointment
* Cancel appointment
* History
* Clear, friendly, forgiving

Each role gets:

* Different nav
* Different landing page
* Same design system

---

## 5️⃣ Frontend ↔ Backend Contract

We will **not improvise APIs**.

We lock:

* Request/response shapes
* Error formats
* Auth headers

### Example

```
Authorization: Bearer <JWT>
```

Errors:

```json
{ "error": "Forbidden" }
```

Frontend handles:

* 401 → login
* 403 → role error
* 429 → rate limit message

---

## 6️⃣ Step-by-Step Frontend Build Plan

### STEP F1 — Project Bootstrap (NO UI YET)

* Vite + Vue 3
* Tailwind
* Folder structure
* Base layout
* Token system

### STEP F2 — Auth & Routing

* Login screens
* Token storage
* Role guards
* Logout flow

### STEP F3 — Design System

* Colors
* Spacing
* Typography
* Buttons
* Inputs
* Alerts

### STEP F4 — Admin UI

* Metrics dashboard
* Tables
* Empty states

### STEP F5 — Doctor UI

* Appointment list
* Complete appointment
* Availability

### STEP F6 — Patient UI

* Booking flow
* Cancellation
* History

### STEP F7 — Polish

* Loading skeletons
* Error states
* Accessibility
* Mobile responsiveness

---

## 7️⃣ VERY IMPORTANT: What We Will NOT Do

🚫 No backend changes unless required
🚫 No UI mockups without tokens
🚫 No CSS sprawl
🚫 No role mixing
🚫 No framework-specific design decisions

---

## ✅ Next Action (ONE STEP ONLY)

We now start **STEP F1 — Frontend Bootstrap**.

I will give you:

1. **Exact folder structure**
2. **Exact Vite commands**
3. **Exact Tailwind config**
4. **Zero UI logic yet**

👉 Say **“Start STEP F1”**

And from here on, I will be **surgically precise** in instructions.



