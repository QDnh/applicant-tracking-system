# PRD: Applicant Tracking System

## Problem Statement

Employees involved in hiring have no central place to track who has applied for which job and where each person stands in the hiring process. Candidates arrive from many places (LinkedIn, referrals, job boards, career fairs, the company website), job openings are opened and closed over time, and one person may be considered for several roles at once. Without a shared system, staff can't reliably answer basic questions: Which jobs are open, and what skills do they need? Who is currently interviewing for Junior Developer? Has Jane already applied for this role? Who rejected this candidate, and when? What happened to this person's other applications after they were hired?

Staff need an internal tool (candidates never log in) that keeps candidate, job and application records consistent, enforces a defined hiring process, and lets them move applicants through it quickly without reloading the page.

## Solution

An internal Django web application, used only by logged-in staff, that:

- Stores **candidates** (basic contact information and how the company first found them), with a lifecycle of Active, Deactivated and Archived, so records can be kept for the long term without cluttering daily work.
- Stores **job openings** that can be opened, closed and reopened, each linked to a shared list of **skills** so overlapping skills between jobs are the same record.
- Records **applications** linking one candidate to one job opening, and enforces that a candidate can't have more than one live application to the same opening.
- Moves each application through a defined **stage workflow** (Applied, Screening, Interview, Final Review, Offer, then Hired, Rejected or Withdrawn) using buttons that update in place with HTMX. Only legal moves are offered, final moves ask for confirmation, and every move is recorded in a permanent **stage history**.
- Provides two working screens: a **job page** listing that job's applications in a table, and a **candidate page** showing that person's active and past applications. Both let staff move stages.

## User Stories

### Access

1. As a staff member, I want to log in before using the system, so that hiring data is only visible to employees.
2. As a staff member, I want full access to every feature once logged in, so that I don't need anyone's permission to do my hiring work.
3. As an administrator, I want to manage staff user accounts through the Django admin, so that I can give and remove access without extra screens being built.

### Candidates

4. As a staff member, I want to create a candidate with first name, last name, email, optional phone, source and optional notes, so that I have a record of each person we're considering.
5. As a staff member, I want to pick the candidate's source from a fixed list (LinkedIn, Referral, Company Website, Job Board, Career Fair, Other), so that source data stays consistent and can be filtered reliably.
6. As a staff member, I want the system to reject a new candidate whose email already exists (ignoring upper/lower case), so that the same person isn't entered twice.
7. As a staff member, I want to edit a candidate's basic information at any time, whatever their status, so that records stay accurate.
8. As a staff member, I want to be taken to the new candidate's page after creating them, so that I can immediately record their application.
9. As a staff member, I want to mark a candidate as Deactivated, so that I can show we expect them to come back later, while their current applications keep going and no new ones can be recorded.
10. As a staff member, I want deactivated candidates to remain in the main candidate list with an "Inactive" badge, so that I can still see them at a glance.
11. As a staff member, I want to Archive a candidate we don't expect to hear from again, so that their record is kept for history but hidden from everyday lists.
12. As a staff member, I want archiving to be blocked while the candidate has active applications, with a message telling me to end them first, so that I decide the correct outcome (Rejected or Withdrawn) for each one.
13. As a staff member, I want to restore an archived or deactivated candidate to Active (or move between any of the three states), so that no status decision is permanent.
14. As a staff member, I want to delete a candidate only when they have no applications, so that I can clean up mistakes and duplicates without ever destroying hiring history.
15. As a staff member, I want deleting a candidate who has applications to be refused with a suggestion to archive instead, so that I understand why and what to do.

### Candidate list

16. As a staff member, I want the candidate list to show Active and Deactivated candidates by default, so that I see the people I might work with.
17. As a staff member, I want a separate Archived tab on the candidate list, so that I can still find archived records when I need them.
18. As a staff member, I want to search candidates by name or email, so that I can quickly find a specific person as the list grows.
19. As a staff member, I want search and the status tab to work together, so that I can, for example, search for "jane" among archived candidates.

### Skills

20. As a staff member, I want a Skills page listing every skill, so that I can see and maintain the shared skill list.
21. As a staff member, I want to add a new skill, so that I can attach it to job openings.
22. As a staff member, I want the system to refuse a skill whose name already exists (ignoring case), so that "Python" and "python" don't become two skills.
23. As a staff member, I want to rename a skill, so that I can fix typos everywhere it's used at once.
24. As a staff member, I want deleting a skill to be blocked while any job opening uses it, with a message saying how many jobs use it, so that skills don't silently disappear from jobs.
25. As a staff member, I want to delete an unused skill, so that the list stays tidy.

### Job openings

26. As a staff member, I want to create a job opening with a title, description, optional department and a set of skills chosen from the shared skill list, so that the role's requirements are recorded.
27. As a staff member, I want to edit a job opening's details and skills, so that postings stay current.
28. As a staff member, I want jobs that share a skill to reference the same skill record, so that I can see overlap between roles.
29. As a staff member, I want to close a job opening, so that no new applications can be recorded for it.
30. As a staff member, I want existing applications on a closed job to keep moving through the stages as normal, so that we can finish interviewing people who already applied.
31. As a staff member, I want a closed job's page to show how many applications are still active, so that I remember to finish them.
32. As a staff member, I want to reopen a closed job freely, without a confirmation, so that I can undo an accidental close or accept more applicants.
33. As a staff member, I want the job page to suggest creating a new opening for a genuinely new hiring round, so that each opening stays one hiring round.
34. As a staff member, I want the job page to show a count of people hired, so that I can tell when a role is filled and close it myself.
35. As a staff member, I want hiring someone to leave the job open, so that roles that hire more than one person still work.

### Job list

36. As a staff member, I want the job list to have Open and Closed tabs, so that I can focus on active hiring.
37. As a staff member, I want to search job openings by title, so that I can find a role quickly.

### Recording applications

38. As a staff member, I want a "Record application" action on a job page that lets me pick a candidate, so that I can log an applicant from the job's point of view.
39. As a staff member, I want an "Apply to a job" action on a candidate page that lets me pick a job, so that I can log an application from the candidate's point of view.
40. As a staff member, I want those pickers to offer only Active candidates and Open jobs, so that I can't create an invalid application by accident.
41. As a staff member, I want those pickers to leave out any candidate and job pair that already has a blocking application, so that I only see valid choices.
42. As a staff member, I want the system to refuse a second application from the same candidate to the same opening while an earlier one is active, so that there are never two simultaneous applications to one job.
43. As a staff member, I want a candidate to be able to apply again to the same opening after their earlier application ended as Rejected or Withdrawn, so that people can be reconsidered.
44. As a staff member, I want a candidate who was Hired for an opening to be permanently blocked from applying to that same opening again, so that a current or past hire isn't recorded as applying for the job they got; a rehire applies to a new opening.
45. As a staff member, I want a candidate to have active applications to several different jobs at once, so that people can be considered for more than one role.
46. As a staff member, I want new applications to start in the Applied stage, with that recorded as the first entry in their history, so that every timeline starts at the beginning.

### Moving applications between stages

47. As a staff member, I want to see each application's current stage clearly, so that I know where every applicant stands.
48. As a staff member, I want to move an application one stage forward, so that it progresses through the hiring process in order.
49. As a staff member, I want to move an application one stage back, so that I can undo a misclick or send someone back for another round.
50. As a staff member, I want to Reject an application from any active stage, so that the company can end the process at any point.
51. As a staff member, I want to "Mark as withdrawn" from any active stage, so that I can record that the candidate chose to leave the process (including declining an offer).
52. As a staff member, I want Hire to be available only from the Offer stage, so that nobody is hired without going through the process.
53. As a staff member, I want only the moves that are legal from the current stage to appear as buttons, so that I can't attempt an invalid move.
54. As a staff member, I want the system to refuse illegal moves even if a request is made directly, so that the rules can't be bypassed.
55. As a staff member, I want Hired, Rejected and Withdrawn to be final, with no buttons and no way to move out, so that outcomes are permanent and trustworthy.
56. As a staff member, I want a confirmation dialog before Hire, Reject or Mark as withdrawn that names the candidate and job and says it can't be undone, so that I don't end an application by accident.
57. As a staff member, I want ordinary forward and back moves to happen with one click and no dialog, so that everyday work stays fast.
58. As a staff member, I want the back button on the left and the forward button to its right, so that button direction matches the direction of the stages.
59. As a staff member, I want stage moves to update the page without a full reload, so that I can work through a pipeline quickly.
60. As a staff member, I want hiring a candidate to automatically mark that candidate's other active applications (to other job openings) as withdrawn, so that other recruiters don't keep working with someone who has already taken a job.
61. As a staff member, I want the Hire confirmation to tell me how many other applications (and for which jobs) will be marked as withdrawn, so that nothing happens without my knowing.
62. As a staff member, I want the hire and its automatic withdrawals to succeed or fail together, so that a candidate is never left Hired with other applications still open.
63. As a staff member, I want other candidates' applications to the same job to be unaffected when someone is hired, so that the job can hire more than one person.
64. As a staff member, I want to keep moving applications for Deactivated candidates, so that their in-progress applications can finish.

### Stage history

65. As a staff member, I want every stage move recorded with the from-stage, to-stage, the staff member who made it and when, so that I can see exactly how each application progressed.
66. As a staff member, I want every move recorded, even rapid back-and-forth clicks, so that the history is a complete and trustworthy record.
67. As a staff member, I want automatic withdrawals caused by a hire to appear in the history, attributed to the staff member who made the hire, so that the timeline explains why they happened.

### Job page (main working screen)

68. As a staff member, I want a job page showing the job's details, status, skills, active count and hired count, so that I understand the role at a glance.
69. As a staff member, I want the job page to list its applications in a table (candidate, source, stage, applied date, move buttons), so that I can work through the pipeline row by row.
70. As a staff member, I want a stage move on the job page to update only that application's row, without rows reordering, so that the table stays stable while I work.
71. As a staff member, I want finished applications to remain in the table, visually dimmed, so that I can still see everyone who applied.

### Candidate page

72. As a staff member, I want a candidate page showing their details, status and source, so that I know who they are.
73. As a staff member, I want an "Active applications" section with each application's job, a progress indicator across the active stages and move buttons, so that I can act on this person's applications directly.
74. As a staff member, I want active applications ordered by applied date, newest first, and never reordered when their stage changes, so that cards don't jump around while I work.
75. As a staff member, I want a "Past applications" section listing Hired, Rejected and Withdrawn applications, dimmed and showing their ending date, so that their history is clear and separate from current work.
76. As a staff member, I want past applications ordered by ending date, newest first, with a hire shown above the withdrawals it caused, so that the most important recent outcome is at the top.
77. As a staff member, I want a candidate who has been hired more than once (for example, a rehire after leaving) to show each hire as a dated past application, so that the history reads clearly rather than looking like a conflict.
78. As a staff member, I want a stage move on the candidate page to refresh the whole applications and history area, so that every card, including ones changed automatically by a hire, is always correct.
79. As a staff member, I want to see the candidate's recent stage history on their page, so that I can review what happened without opening each job.

## Implementation Decisions

### Stack and structure
- Python and Django with SQLite, managed with uv. Styling is Tailwind CSS with DaisyUI through django-tailwind-cli, interactivity uses HTMX, linting and formatting use Ruff, and tests use pytest.
- Django's built-in authentication. Every view requires login, there are no roles or per-object permissions, and staff accounts are managed in the Django admin.

### Models
- **Candidate**
  - Fields: first name, last name, email, optional phone, source, optional notes, status, and created/updated timestamps.
  - Email is required and unique, and is normalised to lowercase before saving so uniqueness ignores case.
  - Source is a fixed choices field (LinkedIn, Referral, Company Website, Job Board, Career Fair, Other). It means "how we first found this person" and is stored on the candidate, not the application.
  - Status is a single choices field with exactly three values (Active, Deactivated, Archived), so impossible combinations can't happen. Any state can change to any other, except that entering Archived requires zero active applications. Status changes have no confirmation dialog.
- **Skill**
  - Fields: name, unique case-insensitively.
  - Deletion is refused while any job opening uses the skill.
- **JobOpening**
  - Fields: title, description, optional department, status (Open/Closed), a plain many-to-many link to Skill, and created/updated timestamps.
  - Status can switch freely in both directions.
  - Closing only stops new applications; it never changes existing ones.
  - Hiring never changes job status.
- **Application**
  - Fields: candidate, job opening, stage, and applied/created/updated timestamps.
  - The link to Candidate is protected, so a candidate with applications can't be deleted at the database level.
  - Stage is a choices field with eight values, grouped as *active* (Applied, Screening, Interview, Final Review, Offer) and *final* (Hired, Rejected, Withdrawn).
  - A conditional database uniqueness constraint on (candidate, job opening) applies to every application whose stage is not Rejected or Withdrawn. So at most one application per pair can be active *or* Hired, and reapplying is possible only after Rejected or Withdrawn.
  - New applications can only be created for Active candidates and Open jobs, checked in the form/service layer. The database constraint is the final safeguard against simultaneous submissions.
- **StageChange** (stage history)
  - Fields: application, from-stage (empty for the initial entry), to-stage, changed-by (staff user), changed-at.
  - One row is written for every stage change, including the initial "→ Applied" when an application is created.
  - Rows are never collapsed, edited or deleted.

### Stage workflow
- A single transition map in code defines legal moves from each stage:
  - one step forward and one step back within the active stages;
  - Rejected and Withdrawn from any active stage;
  - Hired only from Offer;
  - nothing from final stages.
- All stage changes go through one model-level move method that:
  - validates the move against the transition map, refusing illegal moves with a clear error;
  - updates the stage and writes the StageChange row.
- When the target is Hired, the move method also moves every *other* active application belonging to the same candidate (to other openings) to Withdrawn, writing a StageChange row for each. Everything runs in one database transaction. All rows from that transaction share one timestamp. Applications of other candidates to the same job are untouched.
- Templates build their buttons from the same transition map, so the UI and the rules can't drift apart.

### Views, URLs and HTMX behaviour
- CRUD views for candidates, job openings and skills.
- Candidate deletion is refused when the candidate has applications, and skill deletion is refused when the skill is in use, each with an explanatory message.
- Candidate status actions (deactivate, archive, restore) enforce the archive rule.
- **Candidate list:** a status tab (Active+Deactivated by default, or Archived) and a GET search box matching name or email (case-insensitive contains). Both are expressed as query parameters, so they combine.
- **Job list:** Open/Closed tabs and a GET search box matching title.
- **Job page:**
  - Shows job details, skills, status toggle, active count, hired count and a hint to create a new opening for a new hiring round.
  - Has a "Record application" form whose candidate picker lists only eligible candidates.
  - Lists applications in a table in a fixed order. Final ones are dimmed, with no buttons.
- **Candidate page:**
  - Shows details, status and actions.
  - Has an "Apply to a job" form whose job picker lists only eligible open jobs.
  - Has an Active section (applied date newest first; stable when stages change) and a Past section (ending date newest first, ties broken with Hired first), plus recent stage history.
- **Stage move endpoint:** a POST that calls the move method and returns a partial chosen by the calling page.
  - From the job page, it returns the single updated table row, which replaces that row.
  - From the candidate page, it returns the whole applications and history section, which replaces that section. This keeps auto-withdrawn cards correct after a hire.
- **Button layout:** back move on the left, forward move to its right. At Offer, the forward position is Hire. Reject and "Mark as withdrawn" follow.
- **Confirmations:** Hire, Reject and "Mark as withdrawn" use the HTMX confirm attribute with a message naming the candidate and job and stating it can't be undone. The Hire message also lists the candidate's other active applications that will be withdrawn. Forward/back moves have no confirmation.
- After a new candidate is created, the user is redirected to that candidate's page.

### Testing focus (pytest)
- Transition map: every legal move is allowed and representative illegal moves are refused, including skipping stages, hiring from a non-Offer stage, and any move out of a final stage.
- Hire side effects: the candidate's other active applications are withdrawn with history rows; other candidates' applications are untouched; and everything rolls back together on failure.
- Uniqueness: a duplicate active application is blocked; reapplying after Rejected or Withdrawn is allowed; reapplying to the same opening after Hired is blocked; applications to different jobs at the same time are allowed.
- Lifecycle rules: email uniqueness ignores case; candidate deletion is protected when applications exist; archiving is blocked with active applications; deactivated candidates can't get new applications but existing ones can still move; closed jobs refuse new applications but allow moves; skill deletion is blocked while in use and skill names are unique ignoring case.
- Views: login is required everywhere; pickers show only eligible options; the stage endpoint returns the correct partial for each page; search and filters work.

## Out of Scope

- Candidate-facing features of any kind (candidate login, self-service application forms, public job board).
- Roles or per-job permissions. All staff have equal access.
- Employment tracking (current employee, employment ended, quit/fired). A rehire is handled by applying to a new opening.
- Skills on candidates, and skill details such as required vs nice-to-have or proficiency level.
- Per-application source tracking.
- Kanban board view.
- Reasons or notes required on Rejected/Withdrawn moves.
- Collapsing or editing stage history.
- History of job open/close events.
- Automatic job closing on hire, and a "number of positions" field.
- Bulk actions, such as closing a job and rejecting all remaining applicants.
- Reporting, analytics and dashboards.
- Email or other notifications.
- Resume/file uploads.

### Future work (agreed as possible later additions)
- Adding a new skill inline from the job form using HTMX.
- Creating a new candidate inside the record-application form.
- Live search-as-you-type on the list pages using HTMX.

## Further Notes

- The two candidate inactive states mean different things. **Deactivated** means "we expect the candidate to reach out again." **Archived** means "we don't expect them to, but we need the record and want it hidden." A candidate is always exactly one of Active, Deactivated or Archived.
- Rejected means the company ended the process. Withdrawn means the candidate did, or became unavailable by being hired elsewhere. Keeping them distinct keeps history and any future reporting meaningful.
- The "block it if it's in use" pattern is used consistently: skills used by jobs, candidates with applications (delete), and candidates with active applications (archive).
- Friction is applied only where an action can't be undone. Final stage moves confirm; reversible actions (forward/back, job open/close, candidate status) don't.
- Two throwaway prototypes informed these decisions and live in the prototypes folder. The stage-transitions prototype predates the decisions on Hired blocking reapplication and auto-withdrawal on hire, so it doesn't reflect them. The stage-UI prototype reflects the final screen decisions. Neither should be promoted to production code.
- Not yet decided: whether job openings can be deleted. Treat this as an open question during planning. The safe default would follow the same in-use pattern (refuse deletion while applications exist).
