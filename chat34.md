## 🔒 HMS — **B1: DOCTOR-SIDE APPOINTMENT LIFECYCLE & PERMISSIONS**

### 🎯 Objective

Define and lock **doctor-facing responsibilities** over appointments so that:

* Doctors can **observe and act** only within their legitimate scope
* State transitions remain **explicit, time-aware, and DB-valid**
* Admin invariants from the previous phase remain **unbreakable**

This phase **adds** doctor capabilities without weakening admin governance.

---

## 🧱 Doctor Authority — Explicit & Bounded

Doctors **do not own** the lifecycle.
They are **participants** with limited, time-scoped actions.

**Doctor can:**

* View their own appointments
* Mark an appointment as **COMPLETED**
* Cancel their own appointment **before start time** (doctor-initiated cancel)

**Doctor cannot:**

* Delete appointments
* Override admin actions
* Mark NO_SHOW
* Modify appointments after end time
* Act on other doctors’ appointments

---

## 🧱 Appointment States — Doctor-Relevant Transitions

### ✅ Allowed Transitions (Doctor-Initiated)

```
BOOKED → COMPLETED
BOOKED → CANCELLED_BY_DOCTOR
```

### ❌ Forbidden Transitions

```
COMPLETED → *
NO_SHOW → *
CANCELLED_BY_ADMIN → *
CANCELLED_BY_DOCTOR → *
```

All forbidden transitions return **409 Conflict**.

---

## 🧱 Database Alignment (LOCKED)

### ✅ Status Enumeration (Final)

```
BOOKED
COMPLETED
CANCELLED_BY_ADMIN
CANCELLED_BY_DOCTOR
NO_SHOW
```

* Enforced via SQLite CHECK constraint
* Doctor-side addition: `CANCELLED_BY_DOCTOR`
* Admin invariants unchanged

---

## 🧱 `routes_doctor.py` — Canonical Responsibilities

### B1.1 — Doctor Appointment List (Read-Only)

```
GET /doctor/appointments
```

**Rules**

* Doctor-only (`require_role("doctor")`)
* Returns **only appointments owned by doctor**
* Deterministic ordering by `start_datetime`
* Optional filters:

  * date
  * status
* No mutations
* No side effects

---

### B1.2 — Mark Appointment as COMPLETED

```
PATCH /doctor/appointments/<id>/complete
```

**Guards**

* Appointment belongs to doctor
* Current status = `BOOKED`
* Current time ≥ `end_datetime`

**Behavior**

* Idempotent
* Writes audit entry on success
* Returns 409 on early or invalid attempts
* No logging on failure

---

### B1.3 — Doctor Cancellation (Pre-Start Only)

```
PATCH /doctor/appointments/<id>/cancel
```

**Guards**

* Appointment belongs to doctor
* Current status = `BOOKED`
* Current time < `start_datetime`

**Behavior**

* Transition: `BOOKED → CANCELLED_BY_DOCTOR`
* Idempotent
* Writes audit entry on success
* Returns 409 on late or invalid attempts

---

## 🧱 Audit Trail — Doctor Actions

* Same audit table as admin
* `actor_role = 'doctor'`
* `actor_id = doctor_id`
* Logged actions:

  * `DOCTOR_COMPLETED_APPOINTMENT`
  * `DOCTOR_CANCELLED_APPOINTMENT`
* Failed attempts are **not logged**

---

## 🧱 Security & Correctness Invariants

* Doctor identity derived **only from JWT**
* Appointment ownership checked at DB query level
* All transitions:

  * Explicit
  * Time-guarded
  * DB-validated
  * Audited on success
* No background jobs
* No shared endpoints with admin

---

## 🔒 Locked Outcomes of B1

* Doctor capabilities are **clear, minimal, and safe**
* Admin lifecycle guarantees remain intact
* No overlap or ambiguity between roles
* System remains deterministic and production-grade

---

### ▶️ Next Instruction (when ready)

Say:

> **“Proceed B1.1 implementation.”**

This will implement **doctor appointment list endpoint** end-to-end.

