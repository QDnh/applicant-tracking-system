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

## 2026-11-02 — Implemented Phase 8: Hire cascade and job hire tracking (TDD for the cascade, its isolation, and rollback)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 8.`
2. (Answer to "Run /tdd?") Yes, use /tdd.
3. Tell you what. Just blitz through these. Check it goes red, make it go green, and give the verdict on if it implements. Stop after each of the three.
4. Next
5. Next
6. Yes
7. Continue
8. (Answers to "Append PROMPTS.md?" and "Commit and push?") Yes, append; Yes, commit and push.

### Summary
- **Outcome:**
  - `Application.move_to` now calls `_withdraw_other_active_applications()` when the target is Hired, inside the hire's transaction. Each of the candidate's other active applications gets a Withdrawn StageChange row by the hiring user, stamped with the hire's timestamp, and is updated to Withdrawn. A new `other_active_applications()` method feeds both the cascade and the Hire confirmation, so the dialog and the side effect can't disagree.
  - The Hire `confirm_message` now names the count and job titles that will be withdrawn (unchanged when there are none). The job page shows "N hired" next to the active count and a new-hiring-round hint linking to the create-job form. Hiring never changes job status.
  - Three TDD cycles in the new `tests/test_hire_cascade.py`: the cascade with shared timestamps, isolation (finished applications, other candidates, job status, a second hire), and rollback on a forced mid-cascade failure. Normal tests cover the confirmation with and without withdrawals and the job page hired count and hint.
  - Results: 156 tests pass; `ruff check` and `ruff format --check` pass.
- **Deviations:**
  - The user skipped the approval stop before each GREEN step and asked Claude to go through each cycle in one go (red, green, verdict), stopping only after each behavior. Otherwise every recommendation was accepted with no follow-up questions.
- **Sideways:**
  - Behaviors 2 and 3 passed on their first run, because behavior 1 already filtered by candidate and active stage and ran inside the transaction. Following the prove-tests-can-fail rule, Claude broke the code each time and showed the tests fail on an assertion before restoring it. For behavior 2 there were three breaks: withdrawing by job, dropping the active-stage filter, and closing the job on hire. For behavior 3 the break moved the cascade outside the atomic block.
  - `ruff check` flagged a `zip()` without `strict=` in the rollback test; fixed with `strict=True`. `ruff format` fixed blank lines and wrapping in the appended tests.

## 2026-11-02 — Implemented Phase 7: Final moves with confirmation (TDD for the final-move transition rules and the job-row buttons with confirmations)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 7.`
2. (Answer to "Run /tdd?") Yes, run /tdd.
3. yes, approved
4. yes, approved
5. yes, move on to behavior 2
6. yes, approved
7. yes, finish the rest of Phase 7
8. Minor thing. Can we change Hired badge to green so it stands out?
9. All good. Next.
10. (Answers to "Append PROMPTS.md?" and "Commit and push?") Yes, append; Yes, commit and push.

### Summary
- **Outcome:**
  - `Application.TRANSITIONS` now adds Rejected and Withdrawn to every active stage and Hired to Offer only; final stages stay out of the map, so `move_to` refuses every move out of them. `Application.moves` tags each move `back`, `forward` (Hire takes the forward slot at Offer) or `end` (Reject, Mark as withdrawn), with a `final` flag and a `confirm` message from the new `confirm_message()` naming the candidate and job and saying it can't be undone. Labels for final moves come from `FINAL_MOVE_LABELS`.
  - `_job_row.html`: back/forward slots as before, then Reject and Mark as withdrawn on a second line of the same grid; `hx-confirm` only on final moves; Hire green, Reject red outline. Finished rows are dimmed (`opacity-50`) with no buttons, and (at the user's request) the Hired stage badge is solid green.
  - Two TDD cycles: final-move rules through both `move_to` and the endpoint (15 cases), and per-stage button sets with confirmations only on final moves (5 cases; replaced the Phase 6 button test). Normal tests cover no moves out of any final stage (24 cases), dimmed button-less final rows on the page and in the endpoint response, and reapplying through real moves (allowed after Rejected/Withdrawn, refused after Hired).
  - Results: 150 tests pass; `ruff check` and `ruff format --check` pass. The user checked the phase in the browser.
- **Deviations:**
  - The user accepted every recommendation. After browser testing they asked for a green Hired badge, which was a one-line template change; Claude noted it still shows at half strength in the dimmed row and offered, without building it, to keep the badge undimmed.
- **Sideways:**
  - Behavior 1's RED came from `move_to` raising its own `ValidationError` on the allowed final moves rather than a failed `assert`; Claude said so when presenting it, and 4 of the 15 cases (Hire from non-Offer stages) passed before any change since nothing could reach Hired yet.
  - The first draft of behavior 1's test created two "Jane Doe" candidates, which would have collided on email; fixed before the first run.
  - `ruff check` flagged one long line in the test file; `ruff format` fixed it.
  - The Phase 6 note about the Moves buttons feeling too wide wasn't raised again this phase; the column stayed `w-80` with the final buttons on a second line.

## 2026-11-02 — Implemented Phase 6: Forward and back stage moves (TDD for the transition map, per-move history rows, and the job-row move endpoint)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 6.`
2. (Answer to "Run /tdd?") Yes, run /tdd.
3. yes, go ahead with those three
4. yes, make it pass
5. yes
6. yes, make it pass
7. yes
8. yes, make it pass
9. yes, go ahead
10. How do I check 5 using shell?
11. Everything work. However, I noticed that the applications' row items move when pressing the moves buttons.
12. The buttons feel to wide. However, the other buttons are eventually going to go there, so maybe I should just bring it up then.
13. (Answer to "Append PROMPTS.md?") Yes, append it.

### Summary
- **Outcome:**
  - Added `Application.TRANSITIONS`, the single transition map (active stages only for now: one step back, then one step forward, in button order), and `Application.move_to(to_stage, user)`. In one transaction it re-reads the current stage under `select_for_update`, refuses moves not in the map with a `ValidationError`, saves the stage and appends one `StageChange` row (from, to, user, `changed_at` = `updated_at`). An `Application.moves` property gives templates the legal moves tagged back/forward.
  - POST-only endpoint `/applications/<pk>/move/` (`MoveStageView`): takes `stage` and `context=job`, returns the `applications/_job_row.html` partial (one `<tr id="application-<pk>">`) swapped by HTMX `outerHTML`; illegal moves, unknown context or a missing stage return 400 and change nothing. The job page table uses the partial with a Moves column ("← Stage" left, "Stage →" right, no confirmation) and shows a hidden error alert when a move is refused.
  - Three TDD cycles, all with a proper RED on assertions: legal/illegal transitions (15 cases), one history row per move including rapid back-and-forth and none on refusal, and the job-context endpoint returning only the updated row with back-before-forward buttons and a 400 on an illegal move. Normal tests cover button sets per stage, stable row order, moves on a closed job for a deactivated candidate, and 405/400/login on the endpoint.
  - Results: 104 tests pass; `ruff check` and `ruff format --check` pass. The user checked the phase in the browser.
- **Deviations:**
  - The user asked how to check stage history (manual step 5) from the shell; Claude gave a shell snippet and pointed out the existing admin inline. Claude's verification steps had been unsure whether StageChange was in the admin instead of checking first.
  - After browser testing the user reported row contents shifting when moving; fixed with a fixed-layout table and fixed back/forward button slots. The user found the buttons too wide and chose to revisit the Moves column width in Phase 7, when Reject/Withdraw/Hire join that cell.
- **Sideways:**
  - The column-shift fix had two template slips: a stray no-op `{% for %}` line was left in, and removing it also deleted the Back slot's opening `<div>`. Claude caught the missing `<div>` by rereading the template after tests had passed (tests don't check HTML structure) and fixed it.
  - One malformed `Edit` call on PROMPTS.md (line-number prefix pasted into the match string) failed harmlessly before this entry was added.

## 2026-11-02 — Implemented Phase 5: Recording applications (TDD for reapply rules, picker eligibility, and record-from-job with first history row)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 5.`
2. (Answer to "Run /tdd?") Yes, run /tdd.
3. approved, go ahead
4. approved, go ahead
5. approved, go ahead
6. I think so.
7. approved, go ahead
8. approved, go ahead
9. approved, go ahead
10. (Sent mid-turn while Claude was breaking and restoring the normal tests) Wait, why are you doing that?
11. Where is the rule saying normal tests require breaking?
12. Yes, please.
13. continue
14. (Answers to "Append PROMPTS.md?" and "Commit and push?") Yes, append it; Yes, commit and push.

### Summary
- **Outcome:**
  - Added the `Application` model (candidate and job FKs with `PROTECT`, eight-value `Stage` choices, `ACTIVE_STAGES`/`NON_BLOCKING_STAGES`, timestamps) with a conditional `UniqueConstraint` on (candidate, job opening) for stages other than Rejected/Withdrawn, and the append-only `StageChange` model; migration `applications/0001`; read-only admin with a history inline.
  - `Application.record()` is the single entry point for new applications: it refuses closed jobs, non-Active candidates and blocking (active or Hired) pairs, then creates the application and its `"" → Applied` StageChange (by the current user) in one transaction, turning a constraint `IntegrityError` into the same validation error. `eligible_candidates(job)` and `eligible_jobs(candidate)` drive both pickers.
  - POST-only record endpoints `/applications/new/from-job/<pk>/` and `/applications/new/from-candidate/<pk>/` redirect back with a message. The job page has the Record application form, an applications table (candidate, source, stage, applied date) and an active-application count (also on closed jobs); the candidate page has Apply to a job and a simple applications list. Deleting a candidate or job with applications is refused (suggesting archive or close). Added `get_absolute_url` to `Candidate` and `JobOpening`.
  - Three TDD cycles, all with a proper RED: reapply rules (6 blocking cases did not raise), picker eligibility (extra deactivated/archived/blocked candidates offered), and record-from-job (no history row written). Fourteen normal tests cover the constraint without validation, several jobs at once, the candidate-page endpoint, direct-POST refusals, inactive candidates, active count, lists, delete blocks, protected FKs, POST-only and login.
  - Results: 79 tests pass; `ruff check` and `ruff format --check` pass. The user checked the phase in the browser.
- **Deviations:**
  - The user stopped Claude mid-turn to ask why it was breaking and restoring the normal tests, then asked where the rule requiring that was. Claude reread the memory, confirmed the rule only covers TDD tests that go green on first run, and agreed it had over-applied it. At the user's request the `MEMORY.md` pointer was reworded to say "TDD test … (not normal tests)".
- **Sideways:**
  - Claude broke and restored code for normal tests (behaviour 1's constraint and several-jobs tests, then nine of the remaining tests) under a misreading of the memory rule. All code was restored and the suite stayed green; the `MEMORY.md` pointer's broader wording caused the misreading.
  - Behaviour 3's first run failed with a `DoesNotExist` exception rather than an assertion; Claude rewrote that check as an assertion on the history list before asking for approval.
  - The login-required test initially used `client` and `logged_in_client` as if separate, but they are the same object, so the "anonymous" POST was logged in; fixed by logging out first.
  - Ruff's DJ012 flagged `get_absolute_url` placed before `save()` on `Candidate`; reordered.

## 2026-11-02 — Implemented Phase 4: Candidates (TDD for email normalisation/uniqueness, list search, and create-redirect to detail)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 4.`
2. (Answer to "Run /tdd?") Yes, run /tdd.
3. yes, approved
4. yes, approved
5. yes, move on to behavior 2
6. Will it not show up if we search a full-name?
7. go with option 2
8. yes, move on to behavior 3
9. Keep it. A safeguard in case something breaks later.
10. (Correction, given when Claude moved on to the remaining tests) I should have specified. Can you break it and make sure it can fail? Then fix things and keep it.
11. verified in the browser, continue
12. (Answer to "Append PROMPTS.md?") Yes, append it.

### Summary
- **Outcome:**
  - Added the `Candidate` model (first/last name, unique email, optional phone, fixed `Source` choices, optional notes, Active/Deactivated/Archived status defaulting to Active, timestamps), migration `candidates/0001`, and admin registration.
  - Built the candidate list (search via `?q=`, archived hidden), create (redirects to the candidate page), detail (details, source label, notes), edit, and delete-confirmation pages (`candidates/forms.py`, `candidates/views.py`, `candidates/urls.py`, four templates); wired `candidates/` into `config/urls.py` and enabled the Candidates nav link.
  - Three TDD cycles. Email normalisation/uniqueness went RED (email stored as typed), then GREEN with `Candidate.save()` lowercasing and `CandidateForm.clean_email()` doing a case-insensitive check excluding self. List search (seven parametrized cases) went RED (unfiltered list), then GREEN with `icontains` on first name, last name, email and a `Concat` "first last" name. The create-redirect/detail test passed on first run.
  - Ten more normal tests: fixed source choices, required fields, new candidates default to Active, edit keeping own email, edit to another candidate's email refused, delete after confirming, archived hidden from list, nav link, and login required on candidate pages.
  - Results: 55 tests pass; `ruff check`, `ruff format --check`, and `makemigrations --check` pass. The user verified the phase in the browser.
- **Deviations:**
  - The user asked whether a full-name search would match. Claude confirmed it would not under the plan's per-field matching and offered three options, recommending matching "first last" as well; the user chose that (option 2), going slightly beyond the plan's wording. A `"jane doe"` case was added to the search test.
  - For behavior 3, Claude recommended keeping the test as a regular test without proving it can fail; the user said keep it, then clarified they wanted it broken first.
- **Sideways:**
  - Behavior 3 was a weak TDD pick: the scaffolding (copied from the jobs pattern) already redirected to the detail page and showed the source label, so the test never went RED. Claude flagged this rather than presenting it as a TDD cycle. At the user's request it temporarily broke the redirect and then the source label, confirmed the test failed on each assertion, restored both, and confirmed GREEN. Claude saved a memory to do this by default in future.
  - Claude's first attempt to append the remaining tests was rejected by the user to do the break-and-restore first; the tests were appended afterward unchanged.
  - One over-long line in `candidates/forms.py` failed `ruff check`/`format --check`; fixed with `ruff format`.

## 2026-11-02 — Implemented Phase 3: Job openings (TDD for skill delete block, list tab/search, and Open/Closed toggle)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 3.`
2. (Answer to "Run /tdd?") Yes, run /tdd.
3. Yep
4. Make it pass
5. Is there a reason why the test doesn't use N>0?
6. Leave it at N=2, move on to behavior 2
7. Make it pass
8. Move on to behavior 3
9. Make it pass
10. Go ahead
11. Two minor things. One, it says "1 job opening use it". Two, there are no checks for duplicate job openings. I think we probably don't need to worry about the second thing though.
12. Looks good. Continue
13. (Answer to "Append PROMPTS.md?") Yes, append.

### Summary
- **Outcome:**
  - Added the `JobOpening` model (title, description, optional department, Open/Closed status defaulting to Open, plain M2M to `Skill` with `related_name="job_openings"`, timestamps), migration `jobs/0001`, and admin registration.
  - Built the job list (Open/Closed tabs + case-insensitive title search via `?status=&q=`, unknown status falls back to Open), create/edit (skills as checkboxes), detail, delete-confirmation, and a POST-only Open/Closed toggle with no confirmation (`jobs/forms.py`, `jobs/views.py`, `jobs/urls.py`, four templates).
  - Three TDD cycles. Skill delete while in use went RED (skill was deleted), then GREEN by counting `skill.job_openings` and redirecting with an error naming N (also blocks the GET confirm page). List tab/search (six parametrized cases) went RED (unfiltered list), then GREEN with status + `title__icontains` filters. Toggle went RED (placeholder accepted GET), then GREEN with `@require_POST` flipping status both ways.
  - Ten more normal tests: create with shared skill records, edit including skills, required fields, form pages render, detail content, skill rename reflected on jobs, in-use skill delete GET redirects, job delete keeps skills, tab links keep search, and login required on job pages.
  - Results: 37 tests pass; `ruff check` and `ruff format --check` pass. The user verified the phase in the browser.
- **Deviations:**
  - The user asked why the skill-delete test didn't cover other values of N; Claude explained N=2 was the smallest count that rules out an existence-only check and offered to parametrize over N=1..3. The user chose to keep N=2.
  - During browser verification the user spotted a grammar bug ("1 job opening use it"), fixed to "1 job opening uses it" / "N job openings use it". The singular case remains untested by choice.
  - The user raised the lack of duplicate job-opening checks and suggested it wasn't needed; Claude agreed (each opening is one hiring round, so repeated titles are intended) and nothing was added.
- **Sideways:**
  - The singular verb-agreement bug slipped through because the approved test only covered N=2; caught by the user in the browser.
  - One non-TDD test expected `&amp;` in the tab link, but Django doesn't escape literal template text; the test was corrected to the plain `&`. A long line in the new tests was reformatted by ruff.
  - `tests/test_layout.py::test_job_list_placeholder_renders_inside_base_layout` still passes but its name is now stale; left unchanged and flagged to the user.

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