#!/bin/bash
set -e

BASE_URL="https://venkateshrr19.atlassian.net"
AUTH="Basic dmVua2F0ZXNocnIuMTlAZ21haWwuY29tOkFUQVRUM3hGZkdGMFRIZGNwYjBGdnU1MEV6WXNBNXFJSnlyZG9hLXlPVUZNOTRsZ3VTZ2Uzb2wtcXR4TVQyRURDa0tkTHk5YlE0WU5EeGt0MEVJbVcyUjdrSlZQX25mc1pIUjhTMlhpeldHbUNUWl8tRHpRNlE3VERmbkpYUkY5aFhGZmhIWVVrLTllWW9TLWRza3VhNjlDMWJRb1hJc3NtRWdieU1vcW84b19UaDE4eDZQaFMzMD1GODBEMjRFMQ=="

create_story () {
  EPIC_KEY="$1"
  SUMMARY="$2"
  DESCRIPTION="$3"

  curl -s -X POST \
    -H "Authorization: $AUTH" \
    -H "Content-Type: application/json" \
    "$BASE_URL/rest/api/3/issue" \
    -d "{
      \"fields\": {
        \"project\": { \"key\": \"HMS\" },
        \"summary\": \"$SUMMARY\",
        \"description\": {
          \"type\": \"doc\",
          \"version\": 1,
          \"content\": [
            {
              \"type\": \"paragraph\",
              \"content\": [
                { \"type\": \"text\", \"text\": \"$DESCRIPTION\" }
              ]
            }
          ]
        },
        \"issuetype\": { \"name\": \"Story\" },
        \"parent\": { \"key\": \"$EPIC_KEY\" }
      }
    }" >/dev/null
}

# HMS-1 — Authentication & RBAC
create_story "HMS-1" "Admin login using JWT" "Admin can login and receive JWT token with admin role"
create_story "HMS-1" "Doctor login using JWT" "Doctor can login and receive JWT token with doctor role"
create_story "HMS-1" "Patient login using JWT" "Patient can login and receive JWT token with patient role"
create_story "HMS-1" "Role-based access enforcement" "APIs reject unauthorized role access"

# HMS-2 — Admin Dashboard
create_story "HMS-2" "Admin dashboard KPIs" "Show total doctors patients and appointments"
create_story "HMS-2" "View all appointments" "Admin can view all upcoming and past appointments"
create_story "HMS-2" "Search doctors" "Search doctors by name or specialization"
create_story "HMS-2" "Search patients" "Search patients by name or ID"
create_story "HMS-2" "Blacklist doctor" "Admin can blacklist a doctor"
create_story "HMS-2" "Blacklist patient" "Admin can blacklist a patient"

# HMS-3 — Doctor Lifecycle
create_story "HMS-3" "View assigned appointments" "Doctor sees assigned appointments"
create_story "HMS-3" "Complete appointment" "Doctor marks appointment completed with diagnosis and treatment"
create_story "HMS-3" "Cancel appointment" "Doctor cancels appointment before start time"
create_story "HMS-3" "Provide availability" "Doctor provides availability for next 7 days"
create_story "HMS-3" "View patient history" "Doctor can view full patient treatment history"

# HMS-4 — Patient Lifecycle
create_story "HMS-4" "Patient registration" "Patient can register"
create_story "HMS-4" "Book appointment" "Patient books appointment with conflict prevention"
create_story "HMS-4" "Cancel appointment" "Patient cancels appointment before start time"
create_story "HMS-4" "Reschedule appointment" "Patient reschedules an appointment"
create_story "HMS-4" "View appointment history" "Patient views appointment history with diagnosis and treatment"
create_story "HMS-4" "Edit patient profile" "Patient can edit profile details"

# HMS-5 — Appointment State Management
create_story "HMS-5" "Prevent overlapping bookings" "Prevent overlapping appointments for same doctor"
create_story "HMS-5" "Enforce appointment states" "Valid appointment state transitions only"
create_story "HMS-5" "Persist appointment history" "Appointment history is immutable"

# HMS-6 — Background Jobs
create_story "HMS-6" "Daily appointment reminders" "Send daily reminders to patients"
create_story "HMS-6" "Monthly doctor activity report" "Generate monthly HTML or PDF report for doctors"
create_story "HMS-6" "CSV export of treatments" "Async CSV export of patient treatment history"
create_story "HMS-6" "Async job completion notification" "Notify user when async job finishes"

# HMS-7 — Performance Optimization
create_story "HMS-7" "Cache admin KPIs" "Cache admin dashboard KPIs"
create_story "HMS-7" "Cache expiry" "Implement cache expiry policies"

# HMS-8 — Academic Submission
create_story "HMS-8" "ER diagram" "Create ER diagram for database"
create_story "HMS-8" "API documentation" "List all API endpoints"
create_story "HMS-8" "Project report" "Write project report within 5 pages"
create_story "HMS-8" "AI usage declaration" "Declare AI or LLM usage"
create_story "HMS-8" "Demo video" "Record and upload demo video"

echo "All stories created successfully."

