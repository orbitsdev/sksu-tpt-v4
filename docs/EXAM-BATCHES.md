# Exam batches (morning and afternoon on the same day)

Oct 31, 2026. Source: the Guidance and Testing Center's transferee TPT announcement (2nd semester, AY 2026–2027):
**Dec 13, 2026 (Sunday) · 1st batch 8:00 AM · 2nd batch 1:00 PM · Testing Room, 2nd Floor, Main Gate, ACCESS Campus.**

## Problem

v4 allows **one exam slot per campus per day** (database unique key and a check in `AddExamSlot`), and the old
system had no times on slots at all. So a second sitting the same day (the 1:00 PM batch) cannot be set up.

## Decision

A **batch** is simply an exam slot with its own time. A campus may have several exam slots on one day
when their **start times differ**. Nothing else changes: each slot keeps its own rooms, seats, closing and
cancelling; students book one slot and get a room and seat in it.

| Rule | Before | After |
|---|---|---|
| Slots per campus per day | 1 | 1 per start time (e.g. 8:00 AM and 1:00 PM) |
| Slot times | copied from the schedule | chosen per slot (defaults to the schedule's times) |
| Same room, same day | n/a | allowed in different batches; refused in the same batch |
| Name shown | "Sun, Dec 13" | "Sun, Dec 13 · Morning batch · 8:00 AM" (batch word only when the day has more than one) |

Batch word from the start time: before 12:00 → Morning, before 5:00 PM → Afternoon, otherwise Evening.

## Changes

1. **Database:** replace the unique key (schedule, campus, exam_date) with (schedule, campus, exam_date, start_time).
2. **AddExamSlot:** takes report and start times (default: the schedule's). Refuses a second slot at the same campus,
   day and start time (any schedule), and a room already used by a slot with the same day and start time.
3. **ExamSlot model:** `batchName()` ("Morning batch") and `when()` ("Sun, Dec 13 · Morning batch · 8:00 AM").
4. **Admin, Exam slots page:** the Add exam slot dialog asks for the report and start times; the table shows the time,
   with the batch name when the day has two or more.
5. **Student:** exam slot list, booking sheet, Home exam card, permit (screen and PDF) show the batch and time.
6. **Cashier** ("Book this slot"), **check-in**, **seat plan** and **reports** use the same label.
7. **Tests:** two batches same day allowed; same time refused; same room same batch refused; labels.

## Out of scope

Different fees per batch, and moving a student between batches in bulk (the office can move one student at a time,
as today).
