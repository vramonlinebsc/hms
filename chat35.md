Below is a **clean, authoritative, copy-pasteable summary** to seed the **next new chat**.

No commentary. No next steps mixed in.

---

# 🔒 HMS — **B1: DOCTOR-SIDE APPOINTMENT LIFECYCLE (LOCKED SUMMARY)**

## 🎯 Scope of This Phase

Objective was to **define, implement, verify, and harden all doctor-facing appointment capabilities** while preserving admin governance invariants.

This phase explicitly ensures that:

* Doctors are **participants, not owners**, of the appointment lifecycle
* Every doctor action is **bounded, time-guarded, explicit, and auditable**
* No doctor capability weakens admin authority or DB-enforced rules

This phase is now **complete and locked**.

---

## 🧱 Doctor Authority Model — Canonical

Doctors have **limited, explicit powers** over appointments they own.

### ✅ Doctors CAN:

* View their own appointments
* Mark an appointment as **COMPLETED** (after it ends)
* Cancel their own appointment **before it starts**

### ❌ Doctors CANNOT:

* Delete appointments
* Modify other doctors’ appointments
* Mark NO_SHOW
* Override admin actions
* Act after lifecycle closure
* Bypass time guards
* Perform implicit or background actions

Doctor authority is **strictly subordinate** to admin governance.

---

## 🧱 Appointment Lifecycle — Final State Model

### ✅ Authoritative States (DB-Enforced)

```
BOOKED
COMPLETED
CANCELLED_BY_ADMIN
CANCELLED_BY_DOCTOR
NO_SHOW
```

* Enforced via SQLite CHECK constraint
* Database remains the final source of truth
* Code cannot violate lifecycle rules

---

## 🧱 Doctor-Side Transitions (LOCKED)

### ✅ Allowed (Doctor-Initiated)

```
BOOKED → COMPLETED
BOOKED → CANCELLED_BY_DOCTOR
```

### ❌ Forbidden

```
COMPLETED → *
NO_SHOW → *
CANCELLED_BY_ADMIN → *
CANCELLED_BY_DOCTOR → *
```

Invalid transitions return **409 Conflict**.

---

## 🧱 `routes_doctor.py` — Final Responsibilities (LOCKED)

### B1.1 — Doctor Appointment List (Read-Only)

```
GET /doctor/appointments
```

**Properties**

* Doctor-only (`require_role("doctor")`)
* Returns **only appointments owned by the doctor**
* Deterministic ordering by `start_datetime`
* Optional filters:

  * `date`
  * `status` (validated)
* No mutations
* No side effects
* No audit logging

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

* Transition: `BOOKED → COMPLETED`
* Idempotent (repeat calls safe)
* Writes audit entry on success only
* Returns:

  * `404` if not found / not owned
  * `409` on early or invalid attempts

---

### B1.3 — Doctor-Initiated Cancellation (Pre-Start)

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
* Writes audit entry on success only
* Returns:

  * `404` if not found / not owned
  * `409` on late or invalid attempts

---

## 🧱 Audit Trail — Doctor Actions

* Uses the same immutable `audit_logs` table as admin
* Entries written **only on successful state transitions**
* Actor fields:

  * `actor_role = 'doctor'`
  * `actor_id = doctor_id`
* Actions logged:

  * `DOCTOR_COMPLETED_APPOINTMENT`
  * `DOCTOR_CANCELLED_APPOINTMENT`
* Failed or rejected attempts leave **no trace**

---

## 🧱 Security & Correctness Invariants

* Doctor identity derived **only from JWT**
* Appointment ownership enforced at the SQL level
* All transitions are:

  * Explicit
  * Time-guarded
  * DB-validated
  * Audited on success
* No deletes anywhere
* No background jobs
* No shared admin/doctor mutation endpoints
* Deterministic, production-grade behavior

---

## 🔒 Final Invariants (Non-Negotiable)

* Doctor actions are minimal, intentional, and traceable
* Admin governance remains absolute
* Database enforces lifecycle correctness
* No silent corruption possible
* Empty responses are valid states
* Code and schema remain a single contract

---

## ▶️ Instruction for New Chat

Paste **this entire summary** and say:

> **“Proceed B2.”**

This will continue with the **patient-side appointment lifecycle and permissions**.

