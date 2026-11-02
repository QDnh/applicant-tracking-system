import re

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from applications.models import Application
from candidates.models import Candidate
from jobs.models import JobOpening
from tests.test_applications import make_candidate, make_job

Stage = Application.Stage


def make_application(stage=Stage.APPLIED, job=None):
    return Application.objects.create(
        candidate=make_candidate(), job_opening=job or make_job(), stage=stage
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("from_stage", "to_stage", "allowed"),
    [
        # Every one-step forward move between active stages.
        (Stage.APPLIED, Stage.SCREENING, True),
        (Stage.SCREENING, Stage.INTERVIEW, True),
        (Stage.INTERVIEW, Stage.FINAL_REVIEW, True),
        (Stage.FINAL_REVIEW, Stage.OFFER, True),
        # Every one-step back move.
        (Stage.SCREENING, Stage.APPLIED, True),
        (Stage.INTERVIEW, Stage.SCREENING, True),
        (Stage.FINAL_REVIEW, Stage.INTERVIEW, True),
        (Stage.OFFER, Stage.FINAL_REVIEW, True),
        # Skipping forward or back, staying put, and unknown stages are refused.
        (Stage.APPLIED, Stage.INTERVIEW, False),
        (Stage.APPLIED, Stage.OFFER, False),
        (Stage.SCREENING, Stage.FINAL_REVIEW, False),
        (Stage.OFFER, Stage.SCREENING, False),
        (Stage.INTERVIEW, Stage.APPLIED, False),
        (Stage.INTERVIEW, Stage.INTERVIEW, False),
        (Stage.APPLIED, "not_a_stage", False),
    ],
)
def test_move_allows_only_one_step_forward_or_back_between_active_stages(
    user, from_stage, to_stage, allowed
):
    application = make_application(stage=from_stage)

    if allowed:
        application.move_to(to_stage, user)
    else:
        with pytest.raises(ValidationError):
            application.move_to(to_stage, user)

    application.refresh_from_db()
    assert application.stage == (to_stage if allowed else from_stage)


@pytest.mark.django_db
def test_every_move_writes_its_own_history_row_and_refused_moves_write_none(user):
    application = make_application(stage=Stage.APPLIED)
    before = timezone.now()

    # Rapid back-and-forth clicks are each recorded, never collapsed.
    for to_stage in (Stage.SCREENING, Stage.APPLIED, Stage.SCREENING, Stage.INTERVIEW):
        application.move_to(to_stage, user)
    with pytest.raises(ValidationError):
        application.move_to(Stage.OFFER, user)

    history = list(application.stage_changes.order_by("pk"))
    assert [(row.from_stage, row.to_stage, row.changed_by) for row in history] == [
        (Stage.APPLIED, Stage.SCREENING, user),
        (Stage.SCREENING, Stage.APPLIED, user),
        (Stage.APPLIED, Stage.SCREENING, user),
        (Stage.SCREENING, Stage.INTERVIEW, user),
    ]
    assert all(before <= row.changed_at <= timezone.now() for row in history)


@pytest.mark.django_db
def test_move_endpoint_from_job_page_returns_only_the_updated_row_and_refuses_illegal_moves(
    logged_in_client,
):
    application = make_application(stage=Stage.SCREENING)
    url = reverse("applications:move", args=[application.pk])

    response = logged_in_client.post(url, {"stage": Stage.INTERVIEW, "context": "job"})

    assert response.status_code == 200
    html = response.content.decode().strip()
    # Just the one table row HTMX swaps in, not a full page.
    assert html.startswith(f'<tr id="application-{application.pk}"')
    assert html.endswith("</tr>")
    assert html.count("<tr") == 1
    assert "<html" not in html
    # The row shows the new stage and the buttons legal from it: Back left of Forward.
    assert "Interview" in html
    assert html.index("← Screening") < html.index("Final Review →")
    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW

    # An illegal move (skipping Final Review) is refused and changes nothing.
    response = logged_in_client.post(url, {"stage": Stage.OFFER, "context": "job"})

    assert response.status_code == 400
    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW
    assert application.stage_changes.count() == 1


def button_labels(html, application):
    """Move-button labels in the given application's job-page row, left to right."""
    row = html[html.index(f'<tr id="application-{application.pk}"') :]
    row = row[: row.index("</tr>")]
    return re.findall(r"<button[^>]*>\s*(.*?)\s*</button>", row, re.S)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("stage", "labels"),
    [
        (Stage.APPLIED, ["Screening →"]),
        (Stage.SCREENING, ["← Applied", "Interview →"]),
        (Stage.INTERVIEW, ["← Screening", "Final Review →"]),
        (Stage.FINAL_REVIEW, ["← Interview", "Offer →"]),
        (Stage.OFFER, ["← Final Review"]),
    ],
)
def test_job_page_rows_show_buttons_from_the_transition_map(logged_in_client, stage, labels):
    application = make_application(stage=stage)

    html = logged_in_client.get(
        reverse("jobs:detail", args=[application.job_opening.pk])
    ).content.decode()

    assert button_labels(html, application) == labels


@pytest.mark.django_db
def test_job_page_row_order_is_unchanged_by_moves(logged_in_client, user):
    job = make_job()
    applications = [
        Application.objects.create(candidate=make_candidate(name, "Smith"), job_opening=job)
        for name in ("Ann", "Ben", "Cal")
    ]
    url = reverse("jobs:detail", args=[job.pk])
    before = [a.pk for a in logged_in_client.get(url).context["applications"]]

    applications[1].move_to(Stage.SCREENING, user)
    applications[1].move_to(Stage.INTERVIEW, user)

    after = [a.pk for a in logged_in_client.get(url).context["applications"]]
    assert after == before


@pytest.mark.django_db
def test_moves_work_on_closed_jobs_and_for_deactivated_candidates(logged_in_client):
    job = make_job(status=JobOpening.Status.CLOSED)
    application = Application.objects.create(
        candidate=make_candidate(status=Candidate.Status.DEACTIVATED), job_opening=job
    )

    response = logged_in_client.post(
        reverse("applications:move", args=[application.pk]),
        {"stage": Stage.SCREENING, "context": "job"},
    )

    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == Stage.SCREENING


@pytest.mark.django_db
def test_move_endpoint_refuses_bad_requests_and_requires_login(logged_in_client):
    application = make_application()
    url = reverse("applications:move", args=[application.pk])

    assert logged_in_client.get(url).status_code == 405
    for data in ({"stage": Stage.SCREENING, "context": "nowhere"}, {"context": "job"}):
        assert logged_in_client.post(url, data).status_code == 400

    logged_in_client.logout()
    response = logged_in_client.post(url, {"stage": Stage.SCREENING, "context": "job"})
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))

    application.refresh_from_db()
    assert application.stage == Stage.APPLIED
    assert not application.stage_changes.exists()
