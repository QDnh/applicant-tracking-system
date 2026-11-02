import pytest
from django.db import IntegrityError
from django.urls import reverse

from skills.models import Skill


@pytest.mark.django_db
def test_skill_list_shows_all_skills_alphabetically_ignoring_case(logged_in_client):
    for name in ("python", "Django", "SQL", "aws"):
        Skill.objects.create(name=name)

    response = logged_in_client.get(reverse("skills:list"))

    assert response.status_code == 200
    names = [skill.name for skill in response.context["skills"]]
    assert names == ["aws", "Django", "python", "SQL"]


@pytest.mark.django_db
def test_nav_links_to_skills_page(logged_in_client):
    html = logged_in_client.get(reverse("jobs:list")).content.decode()

    assert f'href="{reverse("skills:list")}"' in html


@pytest.mark.django_db
def test_add_and_rename_pages_render(logged_in_client):
    skill = Skill.objects.create(name="Python")

    assert logged_in_client.get(reverse("skills:create")).status_code == 200
    assert logged_in_client.get(reverse("skills:update", args=[skill.pk])).status_code == 200


@pytest.mark.django_db
def test_valid_skill_can_be_added_and_renamed(logged_in_client):
    response = logged_in_client.post(reverse("skills:create"), {"name": "Pyhton"})
    assert response.status_code == 302
    assert response["Location"] == reverse("skills:list")
    skill = Skill.objects.get()
    assert skill.name == "Pyhton"

    response = logged_in_client.post(reverse("skills:update", args=[skill.pk]), {"name": "Python"})
    assert response.status_code == 302
    skill.refresh_from_db()
    assert skill.name == "Python"


@pytest.mark.django_db
def test_database_rejects_duplicate_name_ignoring_case():
    Skill.objects.create(name="Python")

    with pytest.raises(IntegrityError):
        Skill.objects.create(name="PYTHON")


@pytest.mark.django_db
def test_adding_skill_with_existing_name_ignoring_case_is_refused(logged_in_client):
    Skill.objects.create(name="Python")

    response = logged_in_client.post(reverse("skills:create"), {"name": "python"})

    assert response.status_code == 200
    assert response.context["form"].errors["name"]
    assert Skill.objects.count() == 1


@pytest.mark.django_db
def test_renaming_skill_ignores_case_against_others_but_not_itself(logged_in_client):
    Skill.objects.create(name="Python")
    skill = Skill.objects.create(name="Django")
    url = reverse("skills:update", args=[skill.pk])

    clash = logged_in_client.post(url, {"name": "PYTHON"})
    assert clash.status_code == 200
    assert clash.context["form"].errors["name"]
    skill.refresh_from_db()
    assert skill.name == "Django"

    recase = logged_in_client.post(url, {"name": "DJANGO"})
    assert recase.status_code == 302
    skill.refresh_from_db()
    assert skill.name == "DJANGO"


@pytest.mark.django_db
def test_unused_skill_is_deleted_only_after_confirming(logged_in_client):
    skill = Skill.objects.create(name="Cobol")
    url = reverse("skills:delete", args=[skill.pk])

    confirm_page = logged_in_client.get(url)
    assert confirm_page.status_code == 200
    assert "Cobol" in confirm_page.content.decode()
    assert Skill.objects.filter(pk=skill.pk).exists()

    response = logged_in_client.post(url)
    assert response.status_code == 302
    assert response["Location"] == reverse("skills:list")
    assert not Skill.objects.filter(pk=skill.pk).exists()
