# SKSU TPT 2026 results CSV: findings

Source: `SKSU TPT RESULT 2026.csv` (9,574 lines, 33 columns).

## What the file contains
- **Results table (cols 1–24):** 8,937 examinees. Name, examinee number, preferred program ("Campus-Program"), then for English, Science, Mathematics, Filipino, Social Studies, ESM Competency, and Overall: Standard Score, Stanine, Qualitative Interpretation.
- **A second, unrelated table glued on (cols 32–33):** 9,572 rows of examinee number + preferred program. Looks like the registration/applicant list.

## Scoring model (reverse-engineered) [Likely]
- Standard scores are mean ≈ 500, clipped to 200–800 → `SS = 500 + 100·z`, clipped. 
- Stanine is a fixed band of SS: 1 = <300, 2 = 300–349, 3 = 350–399 … 8 = 600–649, 9 = ≥650 (50-point bands = 0.5 SD). 
- Interpretation maps 1:1 from stanine (Low, Below Average, Low Average, Middle Average, High Average, Above Average, Outstanding…). No inconsistencies found across all 7 score groups. [Certain]
- **Raw scores are not in the export.** Without them nobody can re-verify any standard score. [Certain]

## Data problems [Certain]
1. Two tables in one sheet. Any import that reads it naively breaks.
2. 635 registered examinees have no result row (absent? not encoded? lost?). The file can't tell which.
3. 2 duplicate examinee numbers in the registration list.
4. 1 examinee's program differs between the two lists.
5. Campus and program are packed into one string ("Isulan-Bachelor of Science in Civil Engineering"); 1 row is "No Preferred Program Identified".
6. Two header rows (merged subject header + column header), BOM at start.
7. Stanine and interpretation are stored, though they are derived. Storing derived values invites drift.

## Distribution
- Campus preference: ACCESS 4,343 · Isulan 1,884 · Tacurong 1,663 · Kalamansig 731 · Bagumbayan 128 · Palimbang 94 · Lutayan 93. 56 distinct campus-programs.
- Overall interpretation: Above Average 2,256 · High Average 1,869 · Middle Average 1,614 · Below Average 1,260 · Low Average 1,150 · Outstanding 561 · Low 227.

## Implication for the rebuild
Store: examinee, registration, campus, program (normalized), raw answers/raw subject scores, and the norming parameters (mean/SD per subject per year). Compute SS, stanine and label on read or in a versioned results snapshot. Track attendance explicitly (registered / present / absent) so "635 missing" can never be ambiguous again.
