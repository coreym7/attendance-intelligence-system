# Attendance Intelligence System

An automated Python-based attendance reporting framework used to track, analyze, and escalate student attendance trends across a K–12 district. This system processes multi-source inputs, applies policy logic (including MED-day exemptions and MSIP 6 guidelines), and outputs weekly insights for intervention teams, district leadership, and compliance partners like the prosecuting attorney’s office.

---

## 🧭 What This System Does

- 📊 **Weekly Attendance Tracking:** Calculates and compares 2-week weighted attendance scores across all active students.
- 🏥 **MED-Day Logic:** Applies full-day and partial-day medical absence exemptions from district-supplied files.
- 🧹 **Inactive Student Filtering:** Filters out withdrawn students for practical reporting, even if MSIP 6 tracks them.
- 🏫 **Building & Interventionist Grouping:** Outputs are split by student building and routed to the correct interventionist’s SharePoint folder.
- 🛠 **Rolling Base File Maintenance:** Uses a 0 / -1 / -2 system to track attendance trends week over week.
- 🧪 **Early-Year Logic Priming:** Automatically handles startup cases (first run, partial week history).
- 🗓 **Semester-Specific Recalculation Tool:** Recalculates attendance using a semester-specific window.
- 📨 **Multilingual Parent/Teacher Conference Letter Generator:** Produces threshold-based letters (<90%) using student language preference (English, Spanish, Chuukese).

---

## 🔗 Table of Contents

1. [System Overview](#system-overview)
2. [Inputs](#inputs)
3. [Processing Logic](#processing-logic)
4. [Outputs](#outputs)
5. [Semester Recalculation Tool](#semester-recalculation-tool)
6. [Multilingual Letter Generator](#multilingual-letter-generator)
7. [SharePoint Routing](#sharepoint-routing)
8. [Status and Future Direction](#status-and-future-direction)

---

## 🧠 System Overview

This system was designed to automate weekly attendance tracking and flagging in a large school district. It reduces manual review time, standardizes MSIP 6 compliance logic, and delivers timely, actionable outputs for intervention teams and district leadership.

---

## 📥 Inputs

- **Weekly attendance extract (YTD)** – district-wide, from SIS
- **Full-day and partial-day MED absence files**
- **Active student roster** – filters out inactive/transferred students
- **Student contact info** – used for letter generation and prosecutor reports

---

## 🔧 Processing Logic

- Compares current week to 1 week ago and 2 weeks ago
- Flags students falling below 90% weighted attendance
- Calculates weighted ADA scores using MSIP 6-aligned logic
- Tracks trends across time, highlighting students whose attendance is improving or declining week to week.
- Drops oldest history point (-3) and shifts week labels:
  - `0 = current`, `-1 = last week`, `-2 = two weeks ago`
- Automatically initializes if 0 or 1 week of history is available

---

## 📤 Outputs

- Reports split by **student building**
- Each interventionist receives a personalized folder update via SharePoint
- Reports include flagged students by threshold group
- Used by school board, district admin, and prosecutor's office

---

## 🗓 Semester Recalculation Tool

- Uses semester start date to filter attendance
- Applies same MED-day logic
- Rebuilds reports for semester-specific views

---

## 📨 Multilingual Letter Generator

- Scans base file for students under 90% in most recent week
- Generates templated letters for:
  - English
  - Spanish
  - Chuukese
- Uses SIS field for written communication language
- Outputs to PDF or DOCX format for print distribution

---

## 🔄 SharePoint Routing

- Each interventionist is mapped to specific buildings
- The script outputs to their assigned **SharePoint folder**, ensuring:
  - Correct visibility
  - No manual sorting
  - Secure delivery

---

## 📌 Status and Future Direction

This system is in full production use internally. Scripts are generalized, but code is not published due to dependency on internal file structure, SharePoint routing, and student-level data. Logic is preserved here for architecture reference and hiring review.
