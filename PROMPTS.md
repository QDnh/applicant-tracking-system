# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-11-02 — Implemented Phase 2: Skills (TDD for case-insensitive uniqueness on add/rename and confirmed delete)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 2.`
2. (Answer to "Run /tdd?") Yes, run /tdd.
3. Yes.
4. I think so.
5. Yes, go ahead.
6. Yes, make it pass.
7. Yes.
8. Yes, make it pass.
9. Yes.
10. Verified.
11. (Answer to "Append PROMPTS.md?") Yes, append it. (Answer to "Commit and push?") Yes, commit and push.

### Summary
- **Outcome:**
  - Added the `Skill` model (alphabetical ignoring case) with a database `UniqueConstraint(Lower("name"))` as the final safeguard (migrations `0001` and `0002`), and registered it in the admin.
  - Built the Skills list, add, rename and delete-confirmation pages (`skills/views.py`, `skills/urls.py`, `skills/forms.py`, three templates), and enabled the Skills nav link.
  - Three TDD cycles. Adding a case-insensitive duplicate went RED (302 instead of 200), then GREEN with a `clean_name` check. Renaming went RED because a skill couldn't change its own capitalization, then GREEN once the check excluded the skill being edited. Delete-after-confirm went RED (POST re-showed the page), then GREEN once POST deletes and redirects.
  - Five more normal tests: alphabetical list, nav link, add/rename pages render, valid add and rename, and the database rejecting a duplicate directly.
  - Results: 19 tests pass; `ruff check` and `ruff format --check` pass. The user verified the phase in the browser.
- **Deviations:**
  - None. The user approved all three TDD behaviours and tests as proposed, and asked no follow-up questions.
- **Sideways:**
  - The cycle 2 test first used a local variable named `django`, which shadowed the module name, and had lines over the length limit. It was renamed and reflowed (same assertions) before being shown for approval.
  - The skill-in-use delete block is deferred to Phase 3, as the plan specifies.

## 2026-11-02 — Implemented Phase 1: scaffold, login and base layout (TDD for login-required and logout)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 1.`
2. (Answer to "Run /tdd?") Yes, run /tdd.
3. Yes.
4. I think that should be good. It'll be a check to make sure whatever we add doesn't break the login code.
5. Why did you use middleware rather than LoginMixin? Just curious.
6. Yes, continue.
7. Go for it.
8. Yes, continue.
9. devtools console?
10. Everything works. Continue.
11. (Answer to "Append PROMPTS.md?") Yes, append it.

### Summary
- **Outcome:**
  - Set up a uv project with Django 6.1, django-tailwind-cli (DaisyUI enabled) and HTMX 2 (CDN), plus Ruff and pytest/pytest-django configured in `pyproject.toml`.
  - Created the `config` project and four empty apps (`skills`, `jobs`, `candidates`, `applications`).
  - Built a base layout with a nav (Jobs; Candidates and Skills greyed out until their phases; Log out as a POST form), a styled login page, a placeholder job list, and a root redirect to `/jobs/`.
  - Two TDD cycles. Login required everywhere went RED (200 instead of 302), then GREEN once `LoginRequiredMiddleware` was added. Logout returning to the login page went RED, then GREEN once `LOGOUT_REDIRECT_URL = "login"` was set.
  - Nine more normal tests: login reachable, `?next=` honoured, wrong password and inactive user refused, root redirect, layout, nav, Tailwind/HTMX loaded, and admin user management.
  - Results: 11 tests pass; `ruff check` and `ruff format --check` pass. The user verified the phase in the browser.
- **Deviations:**
  - None from recommendations. The user approved both TDD behaviours and both tests as proposed.
  - Follow-up questions: why I used middleware rather than `LoginRequiredMixin` (answer: the plan specifies it, protection is on by default, and one rule covers function and class views), and what the DevTools console is.
- **Sideways:**
  - `uv init` found the parent `CIDM3312` uv workspace and added this project to its members, which edited `../pyproject.toml` and `../uv.lock` outside the repo. This matches the user's other class projects, so it was kept and disclosed.
  - A first shell probe of the login pages returned 400 because the test host wasn't in `ALLOWED_HOSTS`. Re-run with a `localhost` host header, it gave the expected results.
  - Ruff flagged Django's generated stub files (unused imports, single quotes); these were auto-fixed.
  - A stray `bash.exe.stackdump` (a Git Bash crash dump) appeared in the repo root. It was left untouched and not committed.

## 2026-11-02 — Grilled the project idea into 18 design decisions, built two prototypes, wrote the PRD

### Prompts
1. `/grill-me @project-idea.md`
2. The requirement I was given didn't specify multiple employee types. Just those whose job is to hire. I suppose Option A, then.
3. I agree that source belongs on Application. I like Option B.
4. Actually, I realized something about Question 2. I put the word applications in the requirements. The requirements I was given say candidates can come from various sources. Does that change anything?
5. I fixed the text in project-idea.md. Although, I'm not still not sure where to store it. Would it even be likely a candidate applies using to different methods?
6. Yes, let's change it to A.
7. Let's go with B. This does still allow Jane to apply for multiple different jobs, right?
8. I agree, I think B is the best option. In case of a withdrawl, we probably want a candidate to have the ability to apply again. I also don't think moving out of terminal stages is a good idea.
9. I was actually just wondering about misclicks or premature progression. Option C feels more realistic.
10. Let's go with B. I like the simplicity.
11. Let's do B.
12. Pause. Let's go back to Question 7. I just thought about what if someone clicks back and forth a bunch of times. Also, could the prototype skill help me visualize this stage movement better?
13. Although, B would be nicer, I think it is more complicated than I want to do. Let's go with Option A after all. Here is the skill for you. /prototype can you prototype the hiring stage transition rules from the latest questions in our grill?
14. I'm looking at the html. Should withdraw be an option for staff? Or is that just for me to test?
15. Do the rules feel right: yes. Should Hired block new applications: yes, but only if it allows a new application after he quit or was fired. We should also probably mark other active applications as withdrawn too if he gets Hired. Also, I agree, let's change it to "Mark as withdrawn".
16. When you outline it like that, I agree and think Option A should work.
17. I agree. Option A.
18. B should be simple enough for what we need.
19. Go with B, mark C as a potential future work, and block deletion of skills in use.
20. Go with C.
21. The requirements given to me mentioned job opening may be allowed to reopen. So B probably works best here.
22. I've noticed a problem. We established that the system would auto mark the other applications as withdrawn when we hire one of the candidates. That means even if we left the job opening open after a hire, all the other applications for that job would be marked withdrawn. We would never be able to hire multiples anyway...
23. Oh, my bad. I miss read that. In that case, I agree with Option A.
24. Let's go with C.
25. I agree. Option A makes the most sense. I assume deactivating probably does the same thing, or something similar.
26. I propose Option C. Keep them as two separate states. Archived sounds more extreme, so deactivated could act as the lighter inactive state, while archived is the heavier inactive state. However, archived would not be a terminal state.
27. Yes, Option A and that table is exactly what I was thinking. Deactivated implies we expect the candidate to reach out again. Archived implies we don't expect the candidate to reach out again, but we need it for the records and want it hidden. In this flow, it makes no sense for it to have both deactivated and archived. So it must be one or the other.
28. Seems it is time for a /prototype.
29. `/prototype UI variations for Question 15: where staff see and move applications between stages. Compare A) a job-opening page with a table (one row per application, stage buttons that swap just that row), B) a Kanban board per job (one column per stage), and C) a candidate page listing their applications. Use Tailwind + DaisyUI styling and the settled stage rules.`
30. Okay. I definitely do not like the Kanban board. Both A and C look good. One thing I think needs to be changed is the progression buttons. Progress forward should be on the right. Progress backward on the left.
31. (Correction, given when rejecting my edit) I meant just swap the progression buttons.
32. Multi-card problem?
33. It looks like it currently swaps fine.
34. Let's do Option B. Both pages look good in the prototype. It would be very convenient to have both in a real setting.
35. Let's go with B, mark C as future work.
36. B with C as future work.
37. I just had a thought. With the current design, if a candidate got hired, all other applications got marked as withdrawn, quit, reapplied, and got hired for a different job wouldn't there be multiple jobs marked "Hired" on their page?
38. I think Option A would actually be enough here. Past applications will end up lower on the list anyway.
39. Oh wait, I didn't think about withdraws and rejections. Option B is better.
40. Could you adjust the prototype so I can make sure I like the look of it?
41. Okay, two things. The cards jump around if I progress one of the lower applications. Those should not move, or it'll get confusing. Also, the most recent Hired ends up below the auto withdrawn ones. Although, I think that is something that can't be fixed due to the order the code runs.
42. Looks good. `/to-prd`
43. Write this session log to PROMPTS.md according to its instructions.

### Summary
- **Outcome:**
  - The grill-me interview settled 18 design decisions: access, candidate source and email uniqueness, the application uniqueness rule, the stage transition rules, terminal-move confirmation, stage history, skills, job close/reopen, candidate lifecycle (Active/Deactivated/Archived), screens, recording applications, list search, and candidate-page ordering.
  - Built two throwaway prototypes: `prototypes/stage-transitions.html` (stage-rule logic walkthrough) and `prototypes/stage-ui.html` (job table, Kanban and candidate page variants).
  - Wrote `prd/applicant-tracking-system.md` (79 user stories).
  - Saved one feedback memory: change only what was asked.
  - Nothing committed.
- **Deviations:**
  - Q2: I recommended putting source on Application. The user then pointed out the original requirement said *candidates* come from sources, so source moved to Candidate (A).
  - Q7a: the user preferred collapsing undo moves (B) but chose recording every move (A) for simplicity.
  - Q4a/4b: the user's own ideas. Hired blocks reapplying to the same opening (a rehire applies to a new opening), and hiring auto-withdraws the candidate's other applications.
  - Q14: the user overrode my recommendation to merge archive/deactivate and proposed two separate, reversible states.
  - Q15: the user chose stage buttons on both the job and candidate pages (B) over my job-page-only recommendation (A). Kanban was rejected.
  - Q18: the user first chose a single list (A), then switched to my recommended Active/Past split (B).
  - Follow-up questions: whether the email rule still allows multiple jobs; how likely different sources per candidate are; whether Withdraw is a real staff action; what the "multi-card problem" was; why the prototype seemed to swap fine.
- **Sideways:**
  - My Q2 recommendation was based on a mis-transcribed requirement. The user caught it and fixed `project-idea.md`.
  - I tried to launch `/prototype` myself and was blocked (user-invoke only), so the user had to run it.
  - When asked to swap the progression buttons, I also regrouped the other buttons. The user rejected the edit; I reverted to the literal change and saved a feedback memory.
  - The UI prototype redraws the whole page on every click, which hid the partial-swap problem I was describing. I hadn't disclosed this until the user noticed.
  - My wording of 4b ("other applications") was ambiguous, and the user misread it as other candidates' applications. It was clarified, and the PRD wording was tightened.
  - My "most recent activity" ordering made candidate-page cards jump. The user caught it, and it was changed to applied date. The user thought the Hired-below-withdrawals ordering couldn't be fixed; it was fixed by changing the write order in the prototype and a tie-break rule in the PRD.
  - Neither prototype was tested, because Node isn't installed.
  - `stage-transitions.html` was left outdated (it predates 4a/4b).
  - Job opening deletion was never decided and is flagged as open in the PRD.