# Results import: how tptv3 does it and how v4 will

**Decision:** v4 does **not** compute scores. The SKSU Testing Center computes them; v4 imports their Excel file, checks it, shows what changes, and publishes on approval.

## How tptv3 imports scores [Certain]

Code: `app/Imports/ExaminationResultImport.php` and `app/Http/Livewire/Admin/Applications/UploadResult.php`.

- **Format:** `.xls` or `.xlsx` only (CSV is refused), loaded with maatwebsite/excel `ToModel`.
- **Columns read by position**, `$row[0]` … `$row[12]`: examinee_number, then raw and standard score for math, english, filipino, science, social studies, then total raw and total standard.
- **Matching key:** none. `examinee_number` is copied in as text. Nothing checks that the number exists, has a permit, or belongs to this examination.

**Flaws:**

1. No `WithHeadingRow`, so the header row itself is saved as a result row.
2. Columns are by position. Any reordered or extra column silently puts scores in the wrong subject.
3. No validation: blank, text, out-of-range or duplicate rows are all saved.
4. Uploading again adds every row a second time; there's no update or replace.
5. No transaction. A failure halfway leaves half the results in.
6. The file isn't kept, and nothing records who uploaded it or when.
7. No check against attendance. Absent examinees and missing answer sheets look the same (the 635 gap).
8. The 2026 file didn't fit this importer: it has name, standard score, stanine and label per subject, ESM, an overall score, and a second table glued on at columns 32–33. Hence the hand-written scripts in `docs/` (`clean_csv.php`, `find_missing_results.php` …) and the Feb 2026 migration adding `esm_*` and `preferred_program`.

## Template

`tpt-scores-template.xlsx` (Download the Excel template on Import scores) follows the **2026 layout**: sheet "Result", two header rows (subject, then Standard Score / Stanine / Qualitative Interpretation per subject), Name of Examinee, Examinee Number, Preferred Program, and one fictional sample row. The importer accepts this layout and the older one-row CSV (`tpt-scores-template.csv`) the same way, through column matching.

## v4 Excel template

Older one-row layout (still accepted, e.g. as CSV).

```csv
examinee_no,name,english_ss,english_stanine,science_ss,science_stanine,math_ss,math_stanine,filipino_ss,filipino_stanine,social_studies_ss,social_studies_stanine,esm_ss,esm_stanine,overall_ss,overall_stanine
500214,"Dela Cruz, Maria Santos",612,8,548,6,571,7,655,9,530,6,566,7,584,7
```

- `name` is only used to double-check the match; the key is `examinee_no`.
- The qualitative label ("Above Average") isn't imported. It comes from the stanine, which matched 1:1 across all of the 2026 data.
- The preferred program isn't imported; it already lives on the application.
- The Testing Center's own Excel is accepted **as it is** (.xlsx or CSV), so they keep their usual export even when the layout changes from year to year:
  - **Sheet:** the sheet with the examinee numbers is picked ("Result" in 2026); the admin can choose another.
  - **Two header rows** (subject, then Standard Score / Stanine) are read together as "English · Standard Score".
  - **Column matching:** each column is matched by its header name, never by position. The admin checks the match once; it is remembered for next year.
  - **Extra columns** (the Qualitative Interpretation, the Preferred Program, the stray list at columns 32–33 in 2026) are set to Ignore.
  - **A required column missing** (examinee number, or a subject's score) stops the import with a plain message. Nothing is saved.

## v4 import rules

| Check | Result |
|---|---|
| Excel quirks: UTF-8 BOM, `;` separators, quoted names with commas, Windows line endings | Handled |
| Examinee number written by Excel as 5.0021E+05, or with spaces | Normalised; anything else that isn't 6 digits is flagged ("letter O instead of zero") |
| Not registered for this schedule | Flagged; not imported |
| Same examinee twice | Flagged; neither row imported until fixed |
| Score outside 200–800, stanine outside 1–9, or stanine not matching the score band | Flagged |
| Has an exam slot but missing from the file | Marked absent on approve (check-in is optional; with it on, a checked-in person with no score is flagged instead) |
| Two tables side by side (the 2026 layout) | The extra columns are ignored in Match columns |
| Re-upload | Compared with what's in the system: new, changed, unchanged. Only approved changes are saved |
| Approval | One transaction. The original file, uploader, time, counts and approver go in `score_imports` and the activity log |
| Publish | A separate step after Prepare result PDFs, now or at a set time; students notified in the app and by email, in waves (SMS later) |
| Correct one score | Edit with a reason; the old value is kept in the history |
