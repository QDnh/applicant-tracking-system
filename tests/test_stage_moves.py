import re
from html import unescape

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


ACTIVE = [Stage.APPLIED, Stage.SCREENING, Stage.INTERVIEW, Stage.FINAL_REVIEW, Stage.OFFER]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("from_stage", "to_stage", "allowed"),
    [
        # Reject and Withdraw end the process from any active stage.
        *[(stage, Stage.REJECTED, True) for stage in ACTIVE],
        *[(stage, Stage.WITHDRAWN, True) for stage in ACTIVE],
        # Hire is only reachable from Offer.
        (Stage.OFFER, Stage.HIRED, True),
        *[(stage, Stage.HIRED, False) for stage in ACTIVE if stage != Stage.OFFER],
    ],
)
def test_final_moves_reject_and_withdraw_from_any_active_stage_and_hire_only_from_offer(
    logged_in_client, user, from_stage, to_stage, allowed
):
    application = make_application(stage=from_stage)

    # Through the model's move method...
    if allowed:
        application.move_to(to_stage, user)
    else:
        with pytest.raises(ValidationError):
            application.move_to(to_stage, user)
    application.refresh_from_db()
    assert application.stage == (to_stage if allowed else from_stage)

    # ...and through a direct request to the endpoint.
    other = Application.objects.create(
        candidate=make_candidate("Sam", "Lee"),
        job_opening=application.job_opening,
        stage=from_stage,
    )
    response = logged_in_client.post(
        reverse("applications:move", args=[other.pk]), {"stage": to_stage, "context": "job"}
    )
    assert response.status_code == (200 if allowed else 400)
    other.refresh_from_db()
    assert other.stage == (to_stage if allowed else from_stage)
    assert other.stage_changes.count() == (1 if allowed else 0)


FINAL = [Stage.HIRED, Stage.REJECTED, Stage.WITHDRAWN]


@pytest.mark.django_db
@pytest.mark.parametrize("from_stage", FINAL)
@pytest.mark.parametrize("to_stage", list(Stage))
def test_no_move_out_of_a_final_stage_is_allowed(user, from_stage, to_stage):
    application = make_application(stage=from_stage)

    with pytest.raises(ValidationError):
        application.move_to(to_stage, user)

    application.refresh_from_db()
    assert application.stage == from_stage
    assert not application.stage_changes.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("to_stage", FINAL)
def test_reapplying_after_a_real_final_move_depends_on_the_outcome(user, to_stage):
    candidate, job = make_candidate(), make_job()
    application = Application.record(candidate, job, user)
    for stage in (Stage.SCREENING, Stage.INTERVIEW, Stage.FINAL_REVIEW, Stage.OFFER, to_stage):
        application.move_to(stage, user)

    if to_stage == Stage.HIRED:
        with pytest.raises(ValidationError):
            Application.record(candidate, job, user)
        assert Application.objects.filter(candidate=candidate, job_opening=job).count() == 1
    else:
        again = Application.record(candidate, job, user)
        assert again.stage == Stage.APPLIED


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


def buttons(html, application):
    """(label, confirm message or None) for each move button in the row, left to right."""
    row = html[html.index(f'<tr id="application-{application.pk}"') :]
    row = row[: row.index("</tr>")]
    found = []
    for attrs, label in re.findall(r"<button([^>]*)>\s*(.*?)\s*</button>", row, re.S):
        confirm = re.search(r'hx-confirm="([^"]*)"', attrs)
        found.append((label, unescape(confirm.group(1)) if confirm else None))
    return found


FINAL_BUTTONS = ["Reject", "Mark as withdrawn"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("stage", "labels"),
    [
        (Stage.APPLIED, ["Screening →", *FINAL_BUTTONS]),
        (Stage.SCREENING, ["← Applied", "Interview →", *FINAL_BUTTONS]),
        (Stage.INTERVIEW, ["← Screening", "Final Review →", *FINAL_BUTTONS]),
        (Stage.FINAL_REVIEW, ["← Interview", "Offer →", *FINAL_BUTTONS]),
        # At Offer, Hire takes the forward position.
        (Stage.OFFER, ["← Final Review", "Hire", *FINAL_BUTTONS]),
    ],
)
def test_job_page_rows_show_buttons_from_the_transition_map_and_confirm_only_final_moves(
    logged_in_client, stage, labels
):
    application = make_application(stage=stage)

    html = logged_in_client.get(
        reverse("jobs:detail", args=[application.job_opening.pk])
    ).content.decode()

    found = buttons(html, application)
    assert [label for label, _ in found] == labels
    for label, confirm in found:
        if label in ("Hire", *FINAL_BUTTONS):
            # Names the candidate and job, and warns it's permanent.
            assert confirm is not None, label
            assert "Jane Doe" in confirm
            assert "Junior Developer" in confirm
            assert "can't be undone" in confirm
        else:
            # Ordinary back/forward moves are one click.
            assert confirm is None, label


def row_tag(html, application):
    start = html.index(f'<tr id="application-{application.pk}"')
    return html[start : html.index(">", start) + 1]


@pytest.mark.django_db
@pytest.mark.parametrize("stage", FINAL)
def test_final_rows_stay_in_the_table_dimmed_with_no_buttons(logged_in_client, stage):
    job = make_job()
    finished = Application.objects.create(candidate=make_candidate(), job_opening=job, stage=stage)
    active = Application.objects.create(candidate=make_candidate("Sam", "Lee"), job_opening=job)

    html = logged_in_client.get(reverse("jobs:detail", args=[job.pk])).content.decode()

    assert buttons(html, finished) == []
    assert "opacity-50" in row_tag(html, finished)
    assert "opacity-50" not in row_tag(html, active)


@pytest.mark.django_db
def test_final_move_from_job_page_returns_the_dimmed_row_without_buttons(logged_in_client):
    application = make_application(stage=Stage.INTERVIEW)

    response = logged_in_client.post(
        reverse("applications:move", args=[application.pk]),
        {"stage": Stage.REJECTED, "context": "job"},
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert "Rejected" in html
    assert "<button" not in html
    assert "opacity-50" in row_tag(html, application)


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
