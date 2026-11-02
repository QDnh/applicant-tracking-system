# CLAUDE.md

Internal, staff-only Django web app for tracking candidates, job openings, and applications through a defined hiring workflow.

## Stack

- Python, Django, SQLite
- Package manager: **uv**
- Tailwind CSS + DaisyUI via django-tailwind-cli
- HTMX for in-page interactivity
- Ruff for linting and formatting
- pytest for tests

## Architecture decisions

- Django built-in auth; every view requires login. No roles or per-object permissions.
- One transition map in code is the single source of truth for legal stage moves. Templates build their stage buttons from that map instead of encoding their own rules.
- Every stage change goes through one model-level move method, which validates against the map, records history, and runs its side effects in a single transaction. Views never set the stage directly.
- Business rules are enforced on the server (form/service layer), with database constraints as the final safeguard. Hiding options in the UI is never the only check.

## References

- PRD (requirements, models, stage rules, deletion and confirmation rules): `prd/applicant-tracking-system.md`
- Implementation plan (phases): `plans/applicant-tracking-system.md`
- Prototypes: `prototypes/` (throwaway; do not promote to production code)

## Maintaining this file

- Only edit this file when the user asks. If something seems worth adding, suggest it instead.
- Add only durable, project-wide facts: verified commands, established conventions, and architecture decisions. Keep the file under ~70 lines.
- Feature rules, phase details, and one-off fixes belong in the PRD, plan, tests, or code, not here.
