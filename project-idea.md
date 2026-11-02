We need to build a new Django application named Applicant Tracking System. This application is an internal tool that will be used by employees that are involved in the hiring process. Both the technology requirements and business requirements are outlined below.

Technology requirments:
- Python
- Django
- SQLite
- uv
- Tailwind CSS with DaisyUI using django-tailwind-cli
- HTMX
- Ruff
- pytest

Business requirements:
- Internal hiring system that will be used by employees; candidates will not log into this system.
- Staff must be able to keep track of candidates and basic candidate information; candidates may come from various sources.
- Staff must be able to create and edit job openings; with job openings either being open or closed.
- Staff must be able to record when a candidate applies for a job opening; a candidate should be allowed to apply for different jobs simultaneously, 
but not multiple simultaneous applications for the same job opening.
- Job application must progress through a defined hiring process; the stages are: Applied, Screening, Interview, Final Review, Offer, Hired, Rejected, and Withdrawn.
- Staff must be able to view the current stage of an applicant in the system, and move applicants between stages; this should not require reloading the page.
- The system must keep track of the skills associated with each job opening; different jobs may have some overlapping skills.
- We will need to decide on how candidate records are managed long-term; for example, when candidates should be edited, archived, deactivated, or removed.
- We will need to decide what happens to applications when a job opening closes; existing applications may be in-progress; a job opening may or may not be allowed to reopen.