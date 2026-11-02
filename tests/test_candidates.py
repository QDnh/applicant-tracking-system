import pytest
from django.urls import reverse

from candidates.models import Candidate


def candidate_data(**overrides):
    data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "phone": "",
        "source": Candidate.Source.LINKEDIN,
        "notes": "",
    }
    return {**data, **overrides}


def make_candidate(first_name, last_name, email, **fields):
    return Candidate.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        source=fields.pop("source", Candidate.Source.LINKEDIN),
        **fields,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("q", "expected"),
    [
        ("", {"Jane Doe", "Mark Janeway", "Ann Lee"}),
        ("JANE", {"Jane Doe", "Mark Janeway"}),
        ("doe", {"Jane Doe"}),
        ("example.org", {"Ann Lee"}),
        ("AnnL", {"Ann Lee"}),
        ("jane doe", {"Jane Doe"}),
        ("zzz", set()),
    ],
)
def test_candidate_list_search_matches_first_name_last_name_or_email(logged_in_client, q, expected):
    make_candidate("Jane", "Doe", "jane@example.com")
    make_candidate("Mark", "Janeway", "mark@example.com")
    make_candidate("Ann", "Lee", "annl@example.org")

    response = logged_in_client.get(reverse("candidates:list"), {"q": q})

    assert response.status_code == 200
    assert {c.full_name for c in response.context["candidates"]} == expected


@pytest.mark.django_db
def test_creating_candidate_redirects_to_their_page_showing_details_and_source(logged_in_client):
    response = logged_in_client.post(
        reverse("candidates:create"),
        candidate_data(
            phone="555-0100",
            source=Candidate.Source.COMPANY_WEBSITE,
            notes="Met at the spring open day.",
        ),
    )

    candidate = Candidate.objects.get()
    detail_url = reverse("candidates:detail", args=[candidate.pk])
    assert response.status_code == 302
    assert response["Location"] == detail_url

    html = logged_in_client.get(detail_url).content.decode()
    for text in (
        "Jane Doe",
        "jane@example.com",
        "555-0100",
        "Company Website",
        "Met at the spring open day.",
    ):
        assert text in html


@pytest.mark.django_db
def test_email_is_saved_lowercase_and_duplicate_ignoring_case_is_refused(logged_in_client):
    url = reverse("candidates:create")

    logged_in_client.post(url, candidate_data(email="Jane.Doe@Example.COM"))
    assert Candidate.objects.get().email == "jane.doe@example.com"

    response = logged_in_client.post(
        url, candidate_data(first_name="Janet", email="JANE.DOE@example.com")
    )

    assert response.status_code == 200
    assert response.context["form"].errors["email"]
    assert Candidate.objects.count() == 1


@pytest.mark.django_db
def test_source_must_be_one_of_the_fixed_choices(logged_in_client):
    assert Candidate.Source.labels == [
        "LinkedIn",
        "Referral",
        "Company Website",
        "Job Board",
        "Career Fair",
        "Other",
    ]

    response = logged_in_client.post(reverse("candidates:create"), candidate_data(source="twitter"))

    assert response.status_code == 200
    assert response.context["form"].errors["source"]
    assert not Candidate.objects.exists()


@pytest.mark.django_db
def test_candidate_requires_names_email_and_source(logged_in_client):
    response = logged_in_client.post(reverse("candidates:create"), {})

    assert response.status_code == 200
    assert set(response.context["form"].errors) == {"first_name", "last_name", "email", "source"}


@pytest.mark.django_db
def test_new_candidate_is_active(logged_in_client):
    logged_in_client.post(reverse("candidates:create"), candidate_data())

    assert Candidate.objects.get().status == Candidate.Status.ACTIVE


@pytest.mark.django_db
def test_candidate_can_be_edited_keeping_own_email(logged_in_client):
    candidate = make_candidate("Jane", "Doe", "jane@example.com")
    url = reverse("candidates:update", args=[candidate.pk])

    assert logged_in_client.get(url).status_code == 200
    response = logged_in_client.post(
        url,
        candidate_data(
            last_name="Smith",
            email="JANE@example.com",
            phone="555-0199",
            source=Candidate.Source.REFERRAL,
            notes="Referred by Sam.",
        ),
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("candidates:detail", args=[candidate.pk])
    candidate.refresh_from_db()
    assert (candidate.last_name, candidate.email, candidate.phone, candidate.source) == (
        "Smith",
        "jane@example.com",
        "555-0199",
        Candidate.Source.REFERRAL,
    )
    assert candidate.notes == "Referred by Sam."


@pytest.mark.django_db
def test_editing_email_to_another_candidates_email_is_refused(logged_in_client):
    make_candidate("Mark", "Janeway", "mark@example.com")
    candidate = make_candidate("Jane", "Doe", "jane@example.com")

    response = logged_in_client.post(
        reverse("candidates:update", args=[candidate.pk]), candidate_data(email="Mark@Example.com")
    )

    assert response.status_code == 200
    assert response.context["form"].errors["email"]
    candidate.refresh_from_db()
    assert candidate.email == "jane@example.com"


@pytest.mark.django_db
def test_candidate_is_deleted_only_after_confirming(logged_in_client):
    candidate = make_candidate("Jane", "Doe", "jane@example.com")
    url = reverse("candidates:delete", args=[candidate.pk])

    confirm_page = logged_in_client.get(url)
    assert confirm_page.status_code == 200
    assert "Jane Doe" in confirm_page.content.decode()
    assert Candidate.objects.exists()

    response = logged_in_client.post(url)

    assert response.status_code == 302
    assert response["Location"] == reverse("candidates:list")
    assert not Candidate.objects.exists()


@pytest.mark.django_db
def test_candidate_list_hides_archived_and_links_to_detail(logged_in_client):
    jane = make_candidate("Jane", "Doe", "jane@example.com")
    make_candidate("Old", "Record", "old@example.com", status=Candidate.Status.ARCHIVED)

    response = logged_in_client.get(reverse("candidates:list"))

    assert [c.full_name for c in response.context["candidates"]] == ["Jane Doe"]
    assert reverse("candidates:detail", args=[jane.pk]) in response.content.decode()


@pytest.mark.django_db
def test_nav_links_to_candidates_page(logged_in_client):
    html = logged_in_client.get(reverse("jobs:list")).content.decode()

    assert f'href="{reverse("candidates:list")}"' in html


@pytest.mark.django_db
def test_candidate_pages_require_login(client):
    candidate = make_candidate("Jane", "Doe", "jane@example.com")
    urls = [
        reverse("candidates:list"),
        reverse("candidates:create"),
        reverse("candidates:detail", args=[candidate.pk]),
        reverse("candidates:update", args=[candidate.pk]),
        reverse("candidates:delete", args=[candidate.pk]),
    ]
    for url in urls:
        response = client.get(url)
        assert response.status_code == 302
        assert response["Location"].startswith(reverse("login"))

    client.post(reverse("candidates:delete", args=[candidate.pk]))
    assert Candidate.objects.exists()
