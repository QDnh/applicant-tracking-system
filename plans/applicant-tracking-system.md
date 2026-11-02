# Plan: Applicant Tracking System

> Source PRD: `prd/applicant-tracking-system.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **Stack**: Python, Django, SQLite, uv, Tailwind CSS + DaisyUI via django-tailwind-cli, HTMX, Ruff, pytest (pytest-django).
- **Project layout**: a `config` project package plus one app per main feature:
  - `skills` — **Skill**
  - `jobs` — **JobOpening** (M2M to `skills.Skill`)
  - `candidates` — **Candidate**
  - `applications` — **Application** and **StageChange**, the stage transition map, the move method, the record-application flows and the stage-move endpoint
  - Dependency direction: `jobs` → `skills`; `applications` → `jobs`, `candidates`. Job and candidate pages render application partials owned by the `applications` app.
- **Models and relationships**:
  - `Skill(name)` — name unique case-insensitively.
  - `JobOpening(title, description, department?, status Open/Closed, skills M2M Skill, created_at, updated_at)` — plain M2M, no through model.
  - `Candidate(first_name, last_name, email, phone?, source, notes?, status Active/Deactivated/Archived, created_at, updated_at)` — email stored lowercase and unique; source is a fixed choices field.
  - `Application(candidate FK PROTECT, job_opening FK PROTECT, stage, applied_at, created_at, updated_at)` — conditional `UniqueConstraint(candidate, job_opening)` where stage is not Rejected or Withdrawn.
  - `StageChange(application FK, from_stage?, to_stage, changed_by FK User, changed_at)` — append-only; never edited, collapsed or deleted.
- **Stage workflow**: one transition map in the `applications` app is the single source of truth for legal moves; one model-level move method performs every stage change; templates build buttons from the map.
- **URLs** (app-namespaced, integer pks, no slugs):
  - `skills:` — `/skills/`, `/skills/new/`, `/skills/<pk>/edit/`, `/skills/<pk>/delete/`
  - `jobs:` — `/jobs/`, `/jobs/new/`, `/jobs/<pk>/`, `/jobs/<pk>/edit/`, `/jobs/<pk>/delete/`, `/jobs/<pk>/toggle-status/`
  - `candidates:` — `/candidates/`, `/candidates/new/`, `/candidates/<pk>/`, `/candidates/<pk>/edit/`, `/candidates/<pk>/delete/`, `/candidates/<pk>/status/`
  - `applications:` — `/applications/new/from-job/<job_pk>/`, `/applications/new/from-candidate/<candidate_pk>/`, `/applications/<pk>/move/` (POST; target stage plus `context=job|candidate`)
  - List filters are GET query parameters (`?status=…&q=…`) so tabs and search combine.
  - Auth: `/accounts/login/`, `/accounts/logout/`; admin at `/admin/`.
- **Authentication / authorization**: Django built-in auth with `LoginRequiredMiddleware` (login required by default everywhere except login). No roles, no per-object permissions. Staff accounts managed in the Django admin.
- **Deletion policy ("block it if it's in use")**: skills used by any job, candidates with any application, and job openings with any application cannot be deleted; each refusal shows an explanatory message.
- **Friction policy**: only irreversible actions (Hire, Reject, Mark as withdrawn) confirm, using `hx-confirm`. Forward/back moves, job open/close and candidate status changes do not.

---

## Phase 1: Scaffold, login and base layout

**User stories**: 1, 2, 3

### What to build

A runnable Django project managed with uv, with Tailwind/DaisyUI compiled via django-tailwind-cli, HTMX loaded in the base template, Ruff configured, and pytest wired up. All four feature apps exist (empty). A base layout with navigation (Jobs, Candidates, Skills, Log out) wraps every page. Login is required for everything; unauthenticated users are redirected to the login page. The Django admin manages staff users. The site root redirects to the job list (a placeholder page until Phase 3).

### Acceptance criteria

- [ ] `uv run python manage.py runserver` starts the app and Tailwind/DaisyUI styles render
- [ ] Visiting any page while logged out redirects to the login page; logging in returns to the requested page
- [ ] Logging out works and returns to the login page
- [ ] A superuser can create and deactivate staff users in the admin
- [ ] `uv run ruff check` and `uv run ruff format --check` pass
- [ ] `uv run pytest` runs, including a test that login is required

---

## Phase 2: Skills

**User stories**: 20, 21, 22, 23, 25

### What to build

The `Skill` model and a Skills page listing every skill alphabetically, with add, rename and delete. Skill names are unique ignoring case, so adding "python" when "Python" exists is refused with a form error. Deleting a skill works (the in-use block arrives with job openings in Phase 3).

### Acceptance criteria

- [ ] Skills page lists all skills and is linked from the nav
- [ ] A skill can be added and renamed
- [ ] Adding or renaming to a name that matches an existing skill ignoring case is refused with a form error
- [ ] An unused skill can be deleted after confirming on a delete page
- [ ] Tests cover case-insensitive uniqueness on create and rename

---

## Phase 3: Job openings

**User stories**: 24, 26, 27, 28, 29, 32, 36, 37

### What to build

The `JobOpening` model with an M2M to `Skill`. Staff can create and edit a job (title, description, optional department, skills chosen from the shared list), view a job detail page showing details, status and skills, and toggle Open/Closed freely with no confirmation. The job list has Open and Closed tabs and a title search that combine via query parameters. Deleting a skill now refuses while any job uses it, stating how many jobs use it. Jobs can be deleted (no applications exist yet; the in-use block arrives in Phase 5).

### Acceptance criteria

- [ ] A job can be created and edited with any set of existing skills; two jobs sharing a skill reference the same Skill record
- [ ] The job detail page shows title, description, department, status and skills
- [ ] Open/Closed toggle works in both directions with no confirmation
- [ ] Job list defaults to the Open tab; the Closed tab shows closed jobs; title search (case-insensitive) works within either tab
- [ ] Deleting a skill used by N jobs is refused with a message naming N; renaming a skill is reflected on every job using it
- [ ] A job can be deleted
- [ ] Tests cover the skill delete block, list tab/search filtering, and the toggle

---

## Phase 4: Candidates

**User stories**: 4, 5, 6, 7, 8, 14, 16, 18, 19

### What to build

The `Candidate` model (status field present, all candidates Active for now). Staff can create a candidate (first/last name, email, optional phone, source from the fixed list, optional notes) and are redirected to that candidate's page. Email is normalised to lowercase, and a duplicate email ignoring case is refused. Candidates can be edited at any time. The candidate list shows non-archived candidates and supports search by name or email via a query parameter that is designed to combine with the status tab added in Phase 10. Candidates can be deleted (none have applications yet).

### Acceptance criteria

- [ ] Creating a candidate redirects to their candidate page showing details and source
- [ ] Source can only be one of LinkedIn, Referral, Company Website, Job Board, Career Fair, Other
- [ ] Email is saved lowercase; creating a candidate whose email matches an existing one ignoring case is refused with a form error
- [ ] A candidate can be edited
- [ ] Candidate list search matches first name, last name or email (case-insensitive contains)
- [ ] A candidate can be deleted
- [ ] Tests cover email normalisation/uniqueness and search

---

## Phase 5: Recording applications

**User stories**: 15, 31, 38, 39, 40, 41, 42, 43, 44, 45, 46

### What to build

The `Application` and `StageChange` models. A "Record application" form on the job page picks a candidate; an "Apply to a job" form on the candidate page picks a job. Pickers offer only Active candidates and Open jobs, and exclude any pair that already has a blocking (active or Hired) application. The form/service layer refuses ineligible pairs, and the conditional unique constraint is the final safeguard. New applications start in Applied with a "→ Applied" StageChange row attributed to the current user. Applications are listed simply on both pages (job page as a table: candidate, source, stage, applied date). The job page shows an active-application count. Deleting a candidate or a job that has any application is refused with a message suggesting archiving (candidate) or closing (job) instead.

### Acceptance criteria

- [ ] An application can be recorded from the job page and from the candidate page
- [ ] Pickers exclude closed jobs and candidates/jobs that already have an active or Hired application for the pair
- [ ] A direct POST of an ineligible pair (closed job, duplicate active application) is refused with an error
- [ ] The database constraint blocks a duplicate active application even when form validation is bypassed
- [ ] Reapplying is allowed after Rejected or Withdrawn and blocked after Hired (set up via fixtures until those moves exist)
- [ ] A candidate can hold active applications to several different jobs
- [ ] Each new application has stage Applied and exactly one StageChange row (empty from-stage → Applied, changed_by = current user)
- [ ] The job page shows the active-application count, including on closed jobs
- [ ] Deleting a candidate or job with applications is refused with an explanatory message; protected FKs enforce it at the database level
- [ ] Tests cover all uniqueness scenarios from the PRD testing focus and picker eligibility

---

## Phase 6: Forward and back stage moves

**User stories**: 30, 47, 48, 49, 57, 58, 59, 64, 65, 66, 69, 70

### What to build

The transition map (active-stage forward/back steps for now) and the model-level move method, which validates against the map, updates the stage and writes a StageChange row. The stage-move endpoint accepts a target stage and `context=job`, calls the move method, and returns the single updated table row, which HTMX swaps in place. The job page table shows each application's current stage as a badge and Back (left) / Forward (right) buttons generated from the map. Moves are one click with no confirmation. Row order is fixed and does not change after a move. Moves work for applications on closed jobs and for any candidate.

### Acceptance criteria

- [ ] Every legal forward and back move between active stages succeeds and writes one StageChange row with from-stage, to-stage, user and timestamp
- [ ] Skipping stages and moving back from Applied are refused by the move method and by the endpoint (error response, nothing changes)
- [ ] Clicking Back/Forward on the job page updates only that row without a full reload; rows don't reorder
- [ ] Back is to the left of Forward; Applied shows no Back
- [ ] Rapid repeated moves each produce their own StageChange row
- [ ] Applications on a closed job can still be moved
- [ ] Tests cover the legal/illegal transitions and that the endpoint returns the row partial for `context=job`

---

## Phase 7: Final moves with confirmation

**User stories**: 50, 51, 52, 53, 54, 55, 56, 71

### What to build

Extend the transition map with Rejected and Withdrawn from every active stage and Hired from Offer only (no cascade yet). On the job page, Offer's forward position becomes Hire; Reject and "Mark as withdrawn" follow the back/forward buttons. Each final move uses an `hx-confirm` message naming the candidate and job and stating it can't be undone. Final stages have no buttons and the move method refuses any move out of them. Finished rows stay in the table, dimmed.

### Acceptance criteria

- [ ] Reject and Mark as withdrawn are available and succeed from every active stage
- [ ] Hire appears only at Offer, in the forward position; hiring from any other stage is refused, even via a direct request
- [ ] Any move out of Hired, Rejected or Withdrawn is refused
- [ ] Hire, Reject and Mark as withdrawn show a confirmation naming the candidate and job and saying it can't be undone; forward/back still have none
- [ ] Final rows are dimmed and show no buttons
- [ ] After Rejected/Withdrawn, the pair can reapply; after Hired, it cannot (verified through the real move flow)
- [ ] Tests cover hire-only-from-Offer, no moves out of final stages, and button sets per stage

---

## Phase 8: Hire cascade and job hire tracking

**User stories**: 33, 34, 35, 60, 61, 62, 63, 67, 68

### What to build

Hiring now also moves every other active application belonging to the same candidate to Withdrawn, writing a StageChange row for each attributed to the hiring user. Everything runs in one transaction and all rows share one timestamp. Other candidates' applications to the same job are untouched, and the job stays open. The Hire confirmation lists how many other applications (and for which jobs) will be withdrawn. The job page shows a hired count and a hint suggesting a new opening for a new hiring round. The job page now shows the full summary: details, status, skills, active count and hired count.

### Acceptance criteria

- [ ] Hiring withdraws the candidate's other active applications, each with a StageChange row by the hiring user sharing the hire's timestamp
- [ ] The candidate's already-final applications and other candidates' applications to the same job are unchanged
- [ ] The job's status is unchanged after a hire; further candidates can still be hired for it
- [ ] If any part of the hire fails, nothing is saved (verified with a forced failure in a test)
- [ ] The Hire confirmation names the count and job titles of applications that will be withdrawn
- [ ] The job page shows the hired count and the new-hiring-round hint
- [ ] Tests cover the cascade, isolation of other candidates, and rollback

---

## Phase 9: Candidate page working screen

**User stories**: 72, 73, 74, 75, 76, 77, 78, 79

### What to build

The candidate page becomes a working screen. It shows details, status and source; an "Active applications" section of cards (job, a progress indicator across the five active stages, move buttons from the transition map with the same confirmations) ordered by applied date newest first and stable across moves; a "Past applications" section (Hired, Rejected, Withdrawn) dimmed with ending date, ordered by ending date newest first with Hired above same-timestamp withdrawals; and recent stage history across all the candidate's applications. The move endpoint with `context=candidate` returns the whole applications and history section, which HTMX swaps, so cards changed by a hire cascade are always correct.

### Acceptance criteria

- [ ] Active cards show job, progress indicator and the correct buttons; ordering is applied date newest first and doesn't change after a move
- [ ] Past applications show ending date, are dimmed, and are ordered by ending date newest first with Hired before withdrawals it caused
- [ ] A candidate hired more than once shows each hire as a separate dated past application
- [ ] A move from the candidate page refreshes the whole applications and history section without a full reload; a hire moves the auto-withdrawn cards into Past immediately
- [ ] Recent stage history lists moves with from/to stage, job, user and time
- [ ] Tests cover section ordering and that the endpoint returns the section partial for `context=candidate`

---

## Phase 10: Candidate lifecycle

**User stories**: 9, 10, 11, 12, 13, 17

### What to build

Candidate status actions on the candidate page let staff switch between Active, Deactivated and Archived freely, with no confirmation, except that Archiving is refused while the candidate has active applications, with a message telling the user to end them first. Deactivated candidates show an "Inactive" badge in the candidate list and on their page, keep their in-progress applications moving, and are excluded from the job page candidate picker and refused by the record-application flows. The candidate list gains an Archived tab, combining with search via query parameters; archived candidates are hidden from the default tab.

### Acceptance criteria

- [ ] Any status can change to any other, except entering Archived with active applications, which is refused with an explanatory message
- [ ] A candidate whose applications are all final can be archived; archived and deactivated candidates can be restored to Active
- [ ] Deactivated candidates appear in the default list with an "Inactive" badge; archived candidates appear only on the Archived tab
- [ ] Search combines with the status tab (e.g. `?status=archived&q=jane`)
- [ ] Deactivated and archived candidates are excluded from pickers and refused for new applications, even via direct request
- [ ] Existing applications of deactivated candidates can still be moved
- [ ] Tests cover the archive block, status transitions, list tab/search combination, and picker exclusion
