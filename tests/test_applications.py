import pytest
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.urls import reverse

from applications.models import Application, StageChange
from candidates.models import Candidate
from jobs.models import JobOpening

Stage = Application.Stage


def make_candidate(first_name="Jane", last_name="Doe", status=Candidate.Status.ACTIVE):
    return Candidate.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=f"{first_name}.{last_name}@example.com".lower(),
        source=Candidate.Source.LINKEDIN,
        status=status,
    )


def make_job(title="Junior Developer", status=JobOpening.Status.OPEN):
    return JobOpening.objects.create(title=title, description="Builds things.", status=status)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("earlier_stage", "allowed"),
    [
        (Stage.APPLIED, False),
        (Stage.SCREENING, False),
        (Stage.INTERVIEW, False),
        (Stage.FINAL_REVIEW, False),
        (Stage.OFFER, False),
        (Stage.HIRED, False),
        (Stage.REJECTED, True),
        (Stage.WITHDRAWN, True),
    ],
)
def test_reapplying_to_same_job_depends_on_how_earlier_application_ended(
    user, earlier_stage, allowed
):
    candidate, job = make_candidate(), make_job()
    # Fixture setup: stage moves don't exist until Phase 6/7.
    Application.objects.create(candidate=candidate, job_opening=job, stage=earlier_stage)

    if allowed:
        Application.record(candidate, job, user)
        assert Application.objects.filter(candidate=candidate, job_opening=job).count() == 2
    else:
        with pytest.raises(ValidationError):
            Application.record(candidate, job, user)
        assert Application.objects.filter(candidate=candidate, job_opening=job).count() == 1


def picker_options(response, field):
    """Labels of the choices the page's record-application picker offers (empty choice excluded)."""
    choices = response.context["record_form"].fields[field].choices
    return {str(label) for value, label in choices if value}


@pytest.mark.django_db
def test_pickers_offer_only_active_candidates_and_open_jobs_without_a_blocking_application(
    logged_in_client,
):
    job = make_job("Junior Developer")
    other_job = make_job("Data Analyst")
    make_candidate("Free", "Agent")
    make_candidate("Gone", "Quiet", status=Candidate.Status.DEACTIVATED)
    make_candidate("Long", "Gone", status=Candidate.Status.ARCHIVED)
    for first, stage in [("Ivy", Stage.INTERVIEW), ("Hal", Stage.HIRED), ("Rex", Stage.REJECTED)]:
        Application.objects.create(
            candidate=make_candidate(first, "Applicant"), job_opening=job, stage=stage
        )
    Application.objects.create(
        candidate=make_candidate("Elsewhere", "Applicant"), job_opening=other_job
    )

    response = logged_in_client.get(reverse("jobs:detail", args=[job.pk]))

    assert picker_options(response, "candidate") == {
        "Free Agent",
        "Rex Applicant",
        "Elsewhere Applicant",
    }

    jane = make_candidate("Jane", "Doe")
    make_job("Fresh Opening")
    make_job("Closed Opening", status=JobOpening.Status.CLOSED)
    for title, stage in [
        ("In Progress", Stage.SCREENING),
        ("Hired Here", Stage.HIRED),
        ("Withdrew Here", Stage.WITHDRAWN),
    ]:
        Application.objects.create(candidate=jane, job_opening=make_job(title), stage=stage)

    response = logged_in_client.get(reverse("candidates:detail", args=[jane.pk]))

    assert picker_options(response, "job_opening") == {
        "Junior Developer",
        "Data Analyst",
        "Fresh Opening",
        "Withdrew Here",
    }


@pytest.mark.django_db
def test_recording_from_job_page_starts_in_applied_with_one_history_row_and_refuses_ineligible(
    logged_in_client, user
):
    job, jane = make_job(), make_candidate()
    url = reverse("applications:record_from_job", args=[job.pk])

    response = logged_in_client.post(url, {"candidate": jane.pk})

    assert response.status_code == 302
    assert response["Location"] == reverse("jobs:detail", args=[job.pk])
    application = Application.objects.get()
    assert (application.candidate, application.job_opening) == (jane, job)
    assert application.stage == Stage.APPLIED
    history = application.stage_changes.values_list("from_stage", "to_stage", "changed_by")
    assert list(history) == [("", Stage.APPLIED, user.pk)]

    # Duplicate while the first is still active: refused.
    logged_in_client.post(url, {"candidate": jane.pk})
    assert Application.objects.count() == 1

    # Closed job: refused even for a candidate with no application.
    closed = make_job("Old Role", status=JobOpening.Status.CLOSED)
    response = logged_in_client.post(
        reverse("applications:record_from_job", args=[closed.pk]), {"candidate": jane.pk}
    )
    assert response["Location"] == reverse("jobs:detail", args=[closed.pk])
    assert not Application.objects.filter(job_opening=closed).exists()
    assert StageChange.objects.count() == 1


@pytest.mark.django_db
def test_database_constraint_blocks_duplicate_active_application_when_validation_is_bypassed():
    candidate, job = make_candidate(), make_job()
    Application.objects.create(candidate=candidate, job_opening=job, stage=Stage.INTERVIEW)

    with pytest.raises(IntegrityError), transaction.atomic():
        Application.objects.create(candidate=candidate, job_opening=job)

    Application.objects.create(candidate=candidate, job_opening=job, stage=Stage.REJECTED)
    assert Application.objects.count() == 2


@pytest.mark.django_db
def test_candidate_can_hold_active_applications_to_several_jobs(user):
    candidate = make_candidate()

    for title in ("Junior Developer", "Data Analyst", "QA Tester"):
        Application.record(candidate, make_job(title), user)

    assert candidate.applications.filter(stage=Stage.APPLIED).count() == 3


@pytest.mark.django_db
def test_recording_from_candidate_page_creates_applied_application_with_history(
    logged_in_client, user
):
    jane, job = make_candidate(), make_job()

    response = logged_in_client.post(
        reverse("applications:record_from_candidate", args=[jane.pk]), {"job_opening": job.pk}
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("candidates:detail", args=[jane.pk])
    application = Application.objects.get()
    assert (application.candidate, application.job_opening, application.stage) == (
        jane,
        job,
        Stage.APPLIED,
    )
    history = application.stage_changes.values_list("from_stage", "to_stage", "changed_by")
    assert list(history) == [("", Stage.APPLIED, user.pk)]


@pytest.mark.django_db
def test_direct_post_from_candidate_page_refuses_closed_job_and_duplicate(logged_in_client):
    jane = make_candidate()
    closed = make_job("Old Role", status=JobOpening.Status.CLOSED)
    taken = make_job("Taken Role")
    Application.objects.create(candidate=jane, job_opening=taken, stage=Stage.OFFER)
    url = reverse("applications:record_from_candidate", args=[jane.pk])

    for job in (closed, taken):
        response = logged_in_client.post(url, {"job_opening": job.pk})
        assert response.status_code == 302
        assert response["Location"] == reverse("candidates:detail", args=[jane.pk])
        assert [str(m) for m in get_messages(response.wsgi_request)], "expected an error message"

    assert Application.objects.count() == 1
    assert not StageChange.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("status", [Candidate.Status.DEACTIVATED, Candidate.Status.ARCHIVED])
def test_inactive_candidate_is_refused_new_applications_even_without_the_form(
    logged_in_client, user, status
):
    candidate, job = make_candidate(status=status), make_job()

    with pytest.raises(ValidationError):
        Application.record(candidate, job, user)

    logged_in_client.post(
        reverse("applications:record_from_candidate", args=[candidate.pk]),
        {"job_opening": job.pk},
    )
    logged_in_client.post(
        reverse("applications:record_from_job", args=[job.pk]), {"candidate": candidate.pk}
    )
    assert not Application.objects.exists()


@pytest.mark.django_db
def test_closed_job_is_refused_by_record_even_without_the_form(user):
    with pytest.raises(ValidationError):
        Application.record(make_candidate(), make_job(status=JobOpening.Status.CLOSED), user)

    assert not Application.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("job_status", [JobOpening.Status.OPEN, JobOpening.Status.CLOSED])
def test_job_page_shows_active_count_and_lists_applications(logged_in_client, job_status):
    job = make_job(status=job_status)
    for first, stage in [
        ("Ann", Stage.APPLIED),
        ("Ben", Stage.OFFER),
        ("Cal", Stage.HIRED),
        ("Dee", Stage.REJECTED),
    ]:
        Application.objects.create(
            candidate=make_candidate(first, "Smith"), job_opening=job, stage=stage
        )

    response = logged_in_client.get(reverse("jobs:detail", args=[job.pk]))

    assert response.context["active_count"] == 2
    html = response.content.decode()
    assert "2</span> active applications" in html
    for text in ("Ann Smith", "Dee Smith", "LinkedIn", "Offer", "Rejected"):
        assert text in html


@pytest.mark.django_db
def test_candidate_page_lists_their_applications(logged_in_client):
    jane = make_candidate()
    Application.objects.create(
        candidate=jane, job_opening=make_job("Data Analyst"), stage=Stage.SCREENING
    )

    html = logged_in_client.get(reverse("candidates:detail", args=[jane.pk])).content.decode()

    assert "Data Analyst" in html
    assert "Screening" in html


@pytest.mark.django_db
def test_deleting_candidate_with_applications_is_refused_suggesting_archive(logged_in_client):
    jane = make_candidate()
    Application.objects.create(candidate=jane, job_opening=make_job(), stage=Stage.REJECTED)
    url = reverse("candidates:delete", args=[jane.pk])

    for response in (logged_in_client.get(url), logged_in_client.post(url)):
        assert response.status_code == 302
        assert response["Location"] == reverse("candidates:detail", args=[jane.pk])
        texts = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Archive" in t for t in texts), texts

    assert Candidate.objects.filter(pk=jane.pk).exists()


@pytest.mark.django_db
def test_deleting_job_with_applications_is_refused_suggesting_close(logged_in_client):
    job = make_job()
    Application.objects.create(candidate=make_candidate(), job_opening=job, stage=Stage.WITHDRAWN)
    url = reverse("jobs:delete", args=[job.pk])

    for response in (logged_in_client.get(url), logged_in_client.post(url)):
        assert response.status_code == 302
        assert response["Location"] == reverse("jobs:detail", args=[job.pk])
        texts = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Close it" in t for t in texts), texts

    assert JobOpening.objects.filter(pk=job.pk).exists()


@pytest.mark.django_db
def test_protected_foreign_keys_block_deleting_candidate_or_job_with_applications():
    candidate, job = make_candidate(), make_job()
    Application.objects.create(candidate=candidate, job_opening=job)

    with pytest.raises(ProtectedError):
        candidate.delete()
    with pytest.raises(ProtectedError):
        job.delete()


@pytest.mark.django_db
def test_record_endpoints_are_post_only_and_require_login(logged_in_client):
    candidate, job = make_candidate(), make_job()
    urls = {
        reverse("applications:record_from_job", args=[job.pk]): {"candidate": candidate.pk},
        reverse("applications:record_from_candidate", args=[candidate.pk]): {"job_opening": job.pk},
    }

    for url in urls:
        assert logged_in_client.get(url).status_code == 405

    logged_in_client.logout()
    for url, data in urls.items():
        response = logged_in_client.post(url, data)
        assert response.status_code == 302
        assert response["Location"].startswith(reverse("login"))

    assert not Application.objects.exists()
