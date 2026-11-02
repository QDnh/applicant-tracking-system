import re

import pytest
from django.urls import reverse

from applications.models import Application, StageChange
from jobs.models import JobOpening
from tests.test_applications import make_candidate, make_job
from tests.test_stage_moves import buttons

Stage = Application.Stage


@pytest.mark.django_db
def test_hiring_withdraws_the_candidates_other_active_applications_with_shared_history(user):
    candidate = make_candidate()
    hired = Application.objects.create(
        candidate=candidate, job_opening=make_job("Junior Developer"), stage=Stage.OFFER
    )
    others = [
        Application.objects.create(candidate=candidate, job_opening=make_job(title), stage=stage)
        for title, stage in (("QA Analyst", Stage.INTERVIEW), ("Support Engineer", Stage.APPLIED))
    ]

    hired.move_to(Stage.HIRED, user)

    hire_row = hired.stage_changes.get()
    for application, from_stage in zip(others, (Stage.INTERVIEW, Stage.APPLIED), strict=True):
        application.refresh_from_db()
        assert application.stage == Stage.WITHDRAWN
        row = application.stage_changes.get()
        assert (row.from_stage, row.to_stage, row.changed_by) == (
            from_stage,
            Stage.WITHDRAWN,
            user,
        )
        # The whole hire shares one timestamp, so the timeline shows why it happened.
        assert row.changed_at == hire_row.changed_at


@pytest.mark.django_db
def test_hiring_leaves_finished_applications_other_candidates_and_the_job_unchanged(user):
    candidate, job = make_candidate(), make_job("Junior Developer")
    hired = Application.objects.create(candidate=candidate, job_opening=job, stage=Stage.OFFER)
    # The candidate's already-finished application elsewhere.
    finished = Application.objects.create(
        candidate=candidate, job_opening=make_job("QA Analyst"), stage=Stage.REJECTED
    )
    # Other candidates' applications to the same job, one at Offer so it can be hired too.
    rival = Application.objects.create(
        candidate=make_candidate("Sam", "Lee"), job_opening=job, stage=Stage.INTERVIEW
    )
    second_hire = Application.objects.create(
        candidate=make_candidate("Ann", "Kim"), job_opening=job, stage=Stage.OFFER
    )

    hired.move_to(Stage.HIRED, user)

    for application, stage in ((finished, Stage.REJECTED), (rival, Stage.INTERVIEW)):
        application.refresh_from_db()
        assert application.stage == stage
        assert not application.stage_changes.exists()
    job.refresh_from_db()
    assert job.status == JobOpening.Status.OPEN

    # The job stays open for more hires.
    second_hire.move_to(Stage.HIRED, user)
    second_hire.refresh_from_db()
    assert second_hire.stage == Stage.HIRED


@pytest.mark.django_db
def test_hire_and_its_withdrawals_roll_back_together_when_any_part_fails(user, monkeypatch):
    candidate = make_candidate()
    hired = Application.objects.create(
        candidate=candidate, job_opening=make_job("Junior Developer"), stage=Stage.OFFER
    )
    others = [
        Application.objects.create(candidate=candidate, job_opening=make_job(title), stage=stage)
        for title, stage in (("QA Analyst", Stage.INTERVIEW), ("Support Engineer", Stage.APPLIED))
    ]

    # Force a failure partway through: the hire and the first withdrawal are written,
    # then writing the second withdrawal's history row blows up.
    real_create = StageChange.objects.create
    withdrawals = []

    def failing_create(**kwargs):
        if kwargs["to_stage"] == Stage.WITHDRAWN:
            withdrawals.append(kwargs)
            if len(withdrawals) == 2:
                raise RuntimeError("database went away")
        return real_create(**kwargs)

    monkeypatch.setattr(StageChange.objects, "create", failing_create)

    with pytest.raises(RuntimeError):
        hired.move_to(Stage.HIRED, user)

    assert len(withdrawals) == 2  # the failure really happened mid-cascade
    for application, stage in (
        (hired, Stage.OFFER),
        *zip(others, (Stage.INTERVIEW, Stage.APPLIED), strict=True),
    ):
        application.refresh_from_db()
        assert application.stage == stage
    assert not StageChange.objects.exists()


@pytest.mark.django_db
def test_hire_confirmation_names_the_count_and_jobs_that_will_be_withdrawn(logged_in_client):
    candidate, job = make_candidate(), make_job("Junior Developer")
    hired = Application.objects.create(candidate=candidate, job_opening=job, stage=Stage.OFFER)
    for title, stage in (("QA Analyst", Stage.INTERVIEW), ("Support Engineer", Stage.APPLIED)):
        Application.objects.create(candidate=candidate, job_opening=make_job(title), stage=stage)
    # Finished applications aren't withdrawn, so they aren't listed.
    Application.objects.create(
        candidate=candidate, job_opening=make_job("Data Analyst"), stage=Stage.REJECTED
    )

    html = logged_in_client.get(reverse("jobs:detail", args=[job.pk])).content.decode()

    confirm = dict(buttons(html, hired))["Hire"]
    assert "Hire Jane Doe for Junior Developer?" in confirm
    assert "2 other active applications as withdrawn: QA Analyst, Support Engineer." in confirm
    assert "Data Analyst" not in confirm
    assert confirm.endswith("This can't be undone.")


@pytest.mark.django_db
def test_hire_confirmation_without_other_applications_mentions_no_withdrawals(user):
    hired = Application.objects.create(
        candidate=make_candidate(), job_opening=make_job(), stage=Stage.OFFER
    )

    assert hired.confirm_message(Stage.HIRED) == (
        "Hire Jane Doe for Junior Developer? This can't be undone."
    )


@pytest.mark.django_db
def test_job_page_shows_hired_count_and_new_hiring_round_hint(logged_in_client, user):
    job = make_job()
    for name in ("Ann", "Ben"):
        application = Application.objects.create(
            candidate=make_candidate(name, "Smith"), job_opening=job, stage=Stage.OFFER
        )
        application.move_to(Stage.HIRED, user)
    Application.objects.create(candidate=make_candidate("Cal", "Smith"), job_opening=job)

    response = logged_in_client.get(reverse("jobs:detail", args=[job.pk]))

    assert response.context["hired_count"] == 2
    assert response.context["active_count"] == 1
    html = response.content.decode()
    assert re.search(r'<span class="font-semibold">2</span>\s*hired', html)
    assert "new hiring round" in html
    assert reverse("jobs:create") in html
