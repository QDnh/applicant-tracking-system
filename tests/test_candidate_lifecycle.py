import pytest
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.urls import reverse

from applications.models import Application
from candidates.models import Candidate
from tests.test_applications import make_candidate, make_job

Status = Candidate.Status
Stage = Application.Stage


def set_status(client, candidate, status):
    return client.post(reverse("candidates:status", args=[candidate.pk]), {"status": status})


def message_texts(response):
    return [str(m) for m in get_messages(response.wsgi_request)]


@pytest.mark.django_db
@pytest.mark.parametrize("from_status", [Status.ACTIVE, Status.DEACTIVATED])
def test_archiving_is_refused_while_candidate_has_active_applications(
    logged_in_client, from_status
):
    jane = make_candidate(status=from_status)
    Application.objects.create(candidate=jane, job_opening=make_job(), stage=Stage.INTERVIEW)

    response = set_status(logged_in_client, jane, Status.ARCHIVED)

    jane.refresh_from_db()
    assert jane.status == from_status
    assert response.status_code == 302
    assert response["Location"] == reverse("candidates:detail", args=[jane.pk])
    texts = message_texts(response)
    assert len(texts) == 1
    assert "can't be archived" in texts[0]
    assert "1 active application" in texts[0]
    assert "Reject or withdraw" in texts[0]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (Status.ACTIVE, Status.DEACTIVATED),
        (Status.ACTIVE, Status.ARCHIVED),
        (Status.DEACTIVATED, Status.ACTIVE),
        (Status.DEACTIVATED, Status.ARCHIVED),
        (Status.ARCHIVED, Status.ACTIVE),
        (Status.ARCHIVED, Status.DEACTIVATED),
    ],
)
def test_status_changes_freely_when_all_applications_are_final(
    logged_in_client, from_status, to_status
):
    jane = make_candidate(status=from_status)
    Application.objects.create(candidate=jane, job_opening=make_job("QA"), stage=Stage.REJECTED)
    Application.objects.create(candidate=jane, job_opening=make_job("Dev"), stage=Stage.HIRED)

    response = set_status(logged_in_client, jane, to_status)

    jane.refresh_from_db()
    assert jane.status == to_status
    assert response["Location"] == reverse("candidates:detail", args=[jane.pk])
    assert message_texts(response) == [f"Jane Doe is now {to_status.label.lower()}."]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({}, {"Jane Active", "Jane Deactivated", "Mark Active", "Mark Deactivated"}),
        ({"q": "jane"}, {"Jane Active", "Jane Deactivated"}),
        ({"status": "archived"}, {"Jane Archived", "Mark Archived"}),
        ({"status": "archived", "q": "jane"}, {"Jane Archived"}),
        ({"status": "bogus", "q": "mark"}, {"Mark Active", "Mark Deactivated"}),
    ],
)
def test_candidate_list_status_tab_combines_with_search(logged_in_client, params, expected):
    for first_name in ("Jane", "Mark"):
        for status in Status:
            make_candidate(first_name, status.label, status=status)

    response = logged_in_client.get(reverse("candidates:list"), params)

    assert {c.full_name for c in response.context["candidates"]} == expected


@pytest.mark.django_db
def test_model_refuses_archiving_with_active_applications_even_without_the_view():
    jane = make_candidate()
    Application.objects.create(candidate=jane, job_opening=make_job(), stage=Stage.OFFER)

    with pytest.raises(ValidationError, match="can't be archived"):
        jane.change_status(Status.ARCHIVED)
    jane.refresh_from_db()
    assert jane.status == Status.ACTIVE

    # ModelForms such as the admin validate through full_clean(), which applies the same rule.
    jane.status = Status.ARCHIVED
    with pytest.raises(ValidationError, match="can't be archived"):
        jane.full_clean()


@pytest.mark.django_db
def test_invalid_status_is_refused_with_a_message(logged_in_client):
    jane = make_candidate()

    response = set_status(logged_in_client, jane, "retired")

    jane.refresh_from_db()
    assert jane.status == Status.ACTIVE
    assert message_texts(response) == ["Choose a valid status."]


@pytest.mark.django_db
def test_deactivated_candidate_shows_inactive_badge_in_list_and_on_page(logged_in_client):
    gone = make_candidate("Gone", "Quiet", status=Status.DEACTIVATED)
    make_candidate("Still", "Here")

    list_html = logged_in_client.get(reverse("candidates:list")).content.decode()
    page_html = logged_in_client.get(reverse("candidates:detail", args=[gone.pk])).content.decode()

    assert list_html.count(">Inactive</span>") == 1
    assert ">Inactive</span>" in page_html
    status_url = reverse("candidates:status", args=[gone.pk])
    assert f'action="{status_url}"' in page_html
    assert 'value="active"' in page_html and 'value="archived"' in page_html
    assert "hx-confirm" not in page_html.split(status_url)[1].split("</form>")[0]
