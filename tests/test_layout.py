import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_site_root_redirects_to_job_list(logged_in_client):
    response = logged_in_client.get("/")

    assert response.status_code == 302
    assert response["Location"] == reverse("jobs:list")


@pytest.mark.django_db
def test_job_list_placeholder_renders_inside_base_layout(logged_in_client):
    response = logged_in_client.get(reverse("jobs:list"))

    assert response.status_code == 200
    templates = [t.name for t in response.templates]
    assert "jobs/job_list.html" in templates
    assert "base.html" in templates


@pytest.mark.django_db
def test_nav_shows_sections_and_logout_form(logged_in_client):
    html = logged_in_client.get(reverse("jobs:list")).content.decode()

    for label in ("Jobs", "Candidates", "Skills", "Log out"):
        assert label in html
    assert f'action="{reverse("logout")}"' in html
    assert 'method="post"' in html


@pytest.mark.django_db
def test_base_layout_loads_tailwind_and_htmx(logged_in_client):
    html = logged_in_client.get(reverse("jobs:list")).content.decode()

    assert "css/tailwind.css" in html
    assert "htmx.org" in html


@pytest.mark.django_db
def test_superuser_can_manage_staff_users_in_admin(client, django_user_model):
    admin = django_user_model.objects.create_superuser("admin", "admin@example.com", "pw")
    client.force_login(admin)

    assert client.get(reverse("admin:auth_user_changelist")).status_code == 200
    assert client.get(reverse("admin:auth_user_add")).status_code == 200
