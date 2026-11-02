import pytest
from django.urls import reverse

from applications.models import Application
from tests.test_applications import make_candidate, make_job

Stage = Application.Stage


def page_url(candidate):
    return reverse("candidates:detail", args=[candidate.pk])


@pytest.mark.django_db
def test_past_applications_are_newest_ending_first_with_a_hire_above_its_withdrawals(
    logged_in_client, user
):
    jane = make_candidate()
    # Created in this order so that neither pk nor applied date gives the expected order.
    withdrawn_before = Application.record(jane, make_job("QA Analyst"), user)
    hired = Application.record(jane, make_job("Junior Developer"), user)
    withdrawn_after = Application.record(jane, make_job("Support Engineer"), user)
    rejected_earlier = Application.record(jane, make_job("Data Analyst"), user)

    rejected_earlier.move_to(Stage.REJECTED, user)
    for stage in (Stage.SCREENING, Stage.INTERVIEW, Stage.FINAL_REVIEW, Stage.OFFER, Stage.HIRED):
        hired.move_to(stage, user)

    past = list(logged_in_client.get(page_url(jane)).context["past_applications"])

    assert past[0] == hired
    assert set(past[1:3]) == {withdrawn_before, withdrawn_after}
    assert past[3] == rejected_earlier


@pytest.mark.django_db
def test_hire_from_candidate_page_returns_the_whole_section_with_withdrawals_in_past(
    logged_in_client, user
):
    jane = make_candidate()
    hired = Application.objects.create(
        candidate=jane, job_opening=make_job("Junior Developer"), stage=Stage.OFFER
    )
    other = Application.objects.create(
        candidate=jane, job_opening=make_job("QA Analyst"), stage=Stage.INTERVIEW
    )

    response = logged_in_client.post(
        reverse("applications:move", args=[hired.pk]),
        {"stage": Stage.HIRED, "context": "candidate"},
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="candidate-applications"' in html
    assert "<html" not in html
    assert list(response.context["active_applications"]) == []
    assert set(response.context["past_applications"]) == {hired, other}
    # The section's history shows the hire and the withdrawal it caused.
    assert {change.to_stage for change in response.context["recent_history"]} == {
        Stage.HIRED,
        Stage.WITHDRAWN,
    }
