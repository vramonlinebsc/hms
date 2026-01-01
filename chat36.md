Below is the **authoritative, copy-pasteable summary** for the next phase.

No commentary. No future steps mixed in.

---

# 🔒 HMS — **B2: PATIENT-SIDE APPOINTMENT LIFECYCLE (LOCKED SUMMARY)**

## 🎯 Scope of This Phase

Objective was to **define, implement, verify, and harden all patient-facing appointment capabilities** while preserving:

* Doctor authority bounds (from B1)
* Absolute admin governance
* Database-enforced lifecycle correctness

Patients are **requesters and participants**, never controllers of lifecycle closure.

This phase is now **complete and locked**.

---

## 🧱 Patient Authority Model — Canonical

Patients have **strictly limited, explicit powers** over appointments they own.

### ✅ Patients CAN:

* View their own appointments
* Create (book) an appointment
* Cancel their own appointment **before it starts**

### ❌ Patients CANNOT:

* Modify appointment times
* Modify doctor assignments
* Complete appointments
* Mark NO_SHOW
* Cancel after start time
* Override admin or doctor actions
* Act on others’ appointments
* Perform implicit or background actions

Patient authority is **strictly subordinate** to doctor actions and admin governance.

---

## 🧱 Appointment Lifecycle — Authoritative State Model

### ✅ States (DB-Enforced, unchanged)

```
BOOKED
COMPLETED
CANCELLED_BY_ADMIN
CANCELLED_BY_DOCTOR
NO_SHOW
```

Patients can influence **only BOOKED → CANCELLED_BY_PATIENT** logically,
but **physically mapped** to existing lifecycle via governance rules.

> ⚠️ There is **NO new state** for patients.

---

## 🧱 Patient-Side Transitions (LOCKED)

### ✅ Allowed (Patient-Initiated)

```
BOOKED → CANCELLED_BY_PATIENT
```

### ❌ Forbidden

```
COMPLETED → *
NO_SHOW → *
CANCELLED_BY_ADMIN → *
CANCELLED_BY_DOCTOR → *
(after start time)
```

Late or invalid attempts return **409 Conflict**.

---

## 🧱 Cancellation Mapping Rule (Critical)

Patient cancellation is **normalized at write time**:

```
BOOKED → CANCELLED_BY_PATIENT
↓
Persisted as → CANCELLED_BY_ADMIN
```

**Rationale**

* Prevents patient-controlled lifecycle states
* Preserves admin-only cancellation semantics
* Avoids schema expansion
* Keeps DB lifecycle minimal and authoritative

Audit trail disambiguates intent.

---

## 🧱 `routes_patient.py` — Final Responsibilities (LOCKED)

### B2.1 — Patient Appointment List (Read-Only)

```
GET /patient/appointments
```

**Properties**

* Patient-only (`require_role("patient")`)
* Returns **only appointments owned by the patient**
* Deterministic ordering by `start_datetime`
* Optional filters:

  * `date`
  * `status` (validated)
* No mutations
* No audit logging

---

### B2.2 — Book Appointment

```
POST /patient/appointments
```

**Guards**

* Patient identity from JWT
* Doctor exists and is active
* Slot exists and is free
* Slot time is in the future

**Behavior**

* Creates appointment in `BOOKED` state
* Idempotent by `(patient_id, doctor_id, start_datetime)`
* No implicit rescheduling
* No side effects

**Returns**

* `201 Created` on success
* `409 Conflict` on slot collision
* `400` on invalid input

---

### B2.3 — Patient-Initiated Cancellation (Pre-Start)

```
PATCH /patient/appointments/<id>/cancel
```

**Guards**

* Appointment belongs to patient
* Current status = `BOOKED`
* Current time < `start_datetime`

**Behavior**

* Logical transition: `BOOKED → CANCELLED_BY_PATIENT`
* Physical write: `CANCELLED_BY_ADMIN`
* Idempotent
* Writes audit entry on success only

**Returns**

* `404` if not found / not owned
* `409` on late or invalid attempts

---

## 🧱 Audit Trail — Patient Actions

* Uses immutable `audit_logs` table
* Written **only on successful transitions**
* Actor fields:

  * `actor_role = 'patient'`
  * `actor_id = patient_id`
* Actions logged:

  * `PATIENT_BOOKED_APPOINTMENT`
  * `PATIENT_CANCELLED_APPOINTMENT`

Audit log is the **only place** patient intent is preserved.

---

## 🧱 Security & Correctness Invariants

* Patient identity derived **only from JWT**
* Ownership enforced at SQL level
* Time guards enforced at mutation time
* No patient-written terminal states
* No deletes
* No background jobs
* No shared mutation endpoints with admin or doctor
* Empty result sets are valid states

---

## 🔒 Final Invariants (Non-Negotiable)

* Patients are requesters, not controllers
* Lifecycle closure remains doctor/admin-only
* Database remains the single source of truth
* Audit logs preserve intent without weakening authority
* Code and schema remain a single contract

---

## ▶️ Instruction for Next Chat

Paste **this entire summary** and say:

> **“Proceed B3.”**

This will continue with **admin-side NO_SHOW enforcement, penalties, and reconciliation**.

