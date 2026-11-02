# CLAUDE.md

Internal, staff-only Django web app for tracking candidates, job openings, and applications through a defined hiring workflow.

## Stack

- Python, Django, SQLite
- Package manager: **uv**
- Tailwind CSS + DaisyUI via django-tailwind-cli
- HTMX for in-page interactivity
- Ruff for linting and formatting
- pytest for tests

## Commands

- Dev server (rebuilds CSS on change): `uv run python manage.py tailwind runserver`
- Build CSS only: `uv run python manage.py tailwind build` (output is gitignored; run after a fresh clone)
- Migrations: `uv run python manage.py makemigrations` then `uv run python manage.py migrate` (run `migrate` after a fresh clone)
- Tests: `uv run pytest`
- Lint/format: `uv run ruff check` and `uv run ruff format --check`

## Conventions

- Views are class-based (Django generic views where they fit); user feedback goes through `django.contrib.messages`.
- HTMX endpoints return a partial template (`_name.html` in the owning app) chosen by the calling page's `context` POST field. A refused action returns 400 with the error message as the body; HTMX doesn't swap it, so the page shows the message in an alert instead.
- Tests live in the top-level `tests/` package (`test_*.py`), with shared fixtures in `tests/conftest.py`.
- This project is a member of the parent `CIDM3312` uv workspace; the `.venv` and `uv.lock` live one folder up.

## Architecture decisions

- Django built-in auth; every view requires login, enforced globally by `LoginRequiredMiddleware`. Don't add per-view login mixins or decorators; a view that must be public is wrapped with `login_not_required` in the URLconf (e.g. `login_not_required(MyView.as_view())`). No roles or per-object permissions.
- One transition map in code is the single source of truth for legal stage moves. Templates build their stage buttons from that map instead of encoding their own rules.
- Every stage change goes through one model-level move method, which validates against the map, records history, and runs its side effects in a single transaction. Views never set the stage directly.
- Every new application is created through one model-level record method (`Application.record()`), which checks eligibility and writes the first stage-history row in a single transaction. Views never create applications directly.
- Every candidate status change goes through one model-level method (`Candidate.change_status()`), which refuses entering Archived while active applications exist. `Candidate.clean()` applies the same rule so the admin can't bypass it. Views never set the status directly.
- Business rules are enforced on the server (form/service layer), with database constraints as the final safeguard. Hiding options in the UI is never the only check.
- Only irreversible actions confirm (`hx-confirm`): Hire, Reject, Mark as withdrawn. Reversible actions (forward/back moves, job open/close, candidate status) never get a dialog.

## References

- PRD (requirements, models, stage rules, deletion and confirmation rules): `prd/applicant-tracking-system.md`
- Implementation plan (phases): `plans/applicant-tracking-system.md`
- Prototypes: `prototypes/` (throwaway; do not promote to production code)

## Maintaining this file

- Only edit this file when the user asks. If something seems worth adding, suggest it instead.
- Add only durable, project-wide facts: verified commands, established conventions, and architecture decisions. Keep the file under ~70 lines.
- Feature rules, phase details, and one-off fixes belong in the PRD, plan, tests, or code, not here.
