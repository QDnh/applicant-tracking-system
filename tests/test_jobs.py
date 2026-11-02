import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from jobs.models import JobOpening
from skills.models import Skill


def make_job(title="Junior Developer", status=JobOpening.Status.OPEN, skills=()):
    job = JobOpening.objects.create(title=title, description="Builds things.", status=status)
    job.skills.set(skills)
    return job


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({}, {"Junior Developer", "Data Analyst"}),
        ({"status": "open"}, {"Junior Developer", "Data Analyst"}),
        ({"status": "closed"}, {"Senior Developer", "Office Manager"}),
        ({"q": "DEVELOPER"}, {"Junior Developer"}),
        ({"status": "closed", "q": "developer"}, {"Senior Developer"}),
        ({"status": "closed", "q": "analyst"}, set()),
    ],
)
def test_job_list_status_tab_and_title_search_combine(logged_in_client, params, expected):
    make_job("Junior Developer")
    make_job("Data Analyst")
    make_job("Senior Developer", status=JobOpening.Status.CLOSED)
    make_job("Office Manager", status=JobOpening.Status.CLOSED)

    response = logged_in_client.get(reverse("jobs:list"), params)

    assert response.status_code == 200
    assert {job.title for job in response.context["jobs"]} == expected


@pytest.mark.django_db
def test_toggle_flips_status_both_ways_and_get_changes_nothing(logged_in_client):
    job = make_job()
    url = reverse("jobs:toggle_status", args=[job.pk])

    response = logged_in_client.get(url)
    assert response.status_code == 405
    job.refresh_from_db()
    assert job.status == JobOpening.Status.OPEN

    response = logged_in_client.post(url)
    assert response.status_code == 302
    assert response["Location"] == reverse("jobs:detail", args=[job.pk])
    job.refresh_from_db()
    assert job.status == JobOpening.Status.CLOSED

    logged_in_client.post(url)
    job.refresh_from_db()
    assert job.status == JobOpening.Status.OPEN


@pytest.mark.django_db
def test_deleting_skill_used_by_jobs_is_refused_with_job_count(logged_in_client):
    python = Skill.objects.create(name="Python")
    make_job("Junior Developer", skills=[python])
    make_job("Data Analyst", skills=[python])

    response = logged_in_client.post(reverse("skills:delete", args=[python.pk]))

    assert Skill.objects.filter(pk=python.pk).exists()
    assert response.status_code == 302
    assert response["Location"] == reverse("skills:list")
    texts = [str(m) for m in get_messages(response.wsgi_request)]
    assert any("2 job openings" in t for t in texts), texts


@pytest.mark.django_db
def test_job_created_with_skills_redirects_to_detail_and_shares_skill_records(logged_in_client):
    python = Skill.objects.create(name="Python")
    sql = Skill.objects.create(name="SQL")
    data = {"title": "Junior Developer", "description": "Builds things.", "department": ""}

    response = logged_in_client.post(
        reverse("jobs:create"), {**data, "skills": [python.pk, sql.pk]}
    )
    junior = JobOpening.objects.get(title="Junior Developer")
    assert response.status_code == 302
    assert response["Location"] == reverse("jobs:detail", args=[junior.pk])
    assert junior.is_open
    assert junior.department == ""

    logged_in_client.post(
        reverse("jobs:create"), {**data, "title": "Data Analyst", "skills": [python.pk]}
    )
    analyst = JobOpening.objects.get(title="Data Analyst")

    assert set(junior.skills.all()) == {python, sql}
    assert list(analyst.skills.all()) == [python]
    assert Skill.objects.count() == 2
    assert set(python.job_openings.all()) == {junior, analyst}


@pytest.mark.django_db
def test_job_can_be_edited_including_its_skills(logged_in_client):
    python = Skill.objects.create(name="Python")
    sql = Skill.objects.create(name="SQL")
    job = make_job(skills=[python])

    response = logged_in_client.post(
        reverse("jobs:update", args=[job.pk]),
        {
            "title": "Mid Developer",
            "description": "Builds more.",
            "department": "Engineering",
            "skills": [sql.pk],
        },
    )

    assert response.status_code == 302
    job.refresh_from_db()
    assert (job.title, job.description, job.department) == (
        "Mid Developer",
        "Builds more.",
        "Engineering",
    )
    assert list(job.skills.all()) == [sql]


@pytest.mark.django_db
def test_job_requires_title_and_description(logged_in_client):
    response = logged_in_client.post(reverse("jobs:create"), {"title": "", "description": ""})

    assert response.status_code == 200
    assert set(response.context["form"].errors) == {"title", "description"}
    assert not JobOpening.objects.exists()


@pytest.mark.django_db
def test_job_form_pages_render(logged_in_client):
    job = make_job()

    assert logged_in_client.get(reverse("jobs:create")).status_code == 200
    assert logged_in_client.get(reverse("jobs:update", args=[job.pk])).status_code == 200


@pytest.mark.django_db
def test_job_detail_shows_details_status_and_skills(logged_in_client):
    job = JobOpening.objects.create(
        title="Junior Developer",
        description="Writes Django code.",
        department="Engineering",
        status=JobOpening.Status.CLOSED,
    )
    job.skills.set([Skill.objects.create(name="Python")])

    html = logged_in_client.get(reverse("jobs:detail", args=[job.pk])).content.decode()

    for text in ("Junior Developer", "Writes Django code.", "Engineering", "Closed", "Python"):
        assert text in html
    assert "Reopen job" in html


@pytest.mark.django_db
def test_renaming_skill_is_reflected_on_every_job_using_it(logged_in_client):
    skill = Skill.objects.create(name="Pyhton")
    jobs = [make_job("Junior Developer", skills=[skill]), make_job("Data Analyst", skills=[skill])]

    logged_in_client.post(reverse("skills:update", args=[skill.pk]), {"name": "Python"})

    for job in jobs:
        html = logged_in_client.get(reverse("jobs:detail", args=[job.pk])).content.decode()
        assert "Python" in html
        assert "Pyhton" not in html


@pytest.mark.django_db
def test_in_use_skill_delete_page_redirects_instead_of_confirming(logged_in_client):
    skill = Skill.objects.create(name="Python")
    make_job(skills=[skill])

    response = logged_in_client.get(reverse("skills:delete", args=[skill.pk]))

    assert response.status_code == 302
    assert response["Location"] == reverse("skills:list")


@pytest.mark.django_db
def test_job_is_deleted_after_confirming_and_its_skills_remain(logged_in_client):
    skill = Skill.objects.create(name="Python")
    job = make_job(skills=[skill])
    url = reverse("jobs:delete", args=[job.pk])

    assert logged_in_client.get(url).status_code == 200
    assert JobOpening.objects.filter(pk=job.pk).exists()

    response = logged_in_client.post(url)

    assert response.status_code == 302
    assert response["Location"] == reverse("jobs:list")
    assert not JobOpening.objects.exists()
    assert Skill.objects.filter(pk=skill.pk).exists()


@pytest.mark.django_db
def test_job_list_tabs_keep_search_and_link_to_detail(logged_in_client):
    job = make_job("Junior Developer")

    html = logged_in_client.get(reverse("jobs:list"), {"q": "junior"}).content.decode()

    assert "?status=closed&q=junior" in html
    assert reverse("jobs:detail", args=[job.pk]) in html


@pytest.mark.django_db
def test_job_pages_require_login(client):
    job = make_job()
    urls = [
        reverse("jobs:list"),
        reverse("jobs:create"),
        reverse("jobs:detail", args=[job.pk]),
        reverse("jobs:update", args=[job.pk]),
        reverse("jobs:delete", args=[job.pk]),
    ]
    for url in urls:
        response = client.get(url)
        assert response.status_code == 302
        assert response["Location"].startswith(reverse("login"))

    client.post(reverse("jobs:toggle_status", args=[job.pk]))
    job.refresh_from_db()
    assert job.is_open
