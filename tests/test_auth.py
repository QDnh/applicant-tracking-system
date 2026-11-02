import pytest
from django.urls import reverse

from tests.conftest import PASSWORD


@pytest.mark.django_db
def test_logged_out_visitor_is_redirected_to_login_with_next(client):
    job_list = reverse("jobs:list")

    response = client.get(job_list)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={job_list}"


@pytest.mark.django_db
def test_logout_returns_to_login_page_and_ends_session(client, user):
    client.force_login(user)

    response = client.post(reverse("logout"))

    assert response.status_code == 302
    assert response["Location"] == reverse("login")
    assert client.get(reverse("jobs:list")).status_code == 302


@pytest.mark.django_db
def test_login_page_is_reachable_while_logged_out(client):
    assert client.get(reverse("login")).status_code == 200


@pytest.mark.django_db
def test_logging_in_returns_to_the_requested_page(client, user):
    job_list = reverse("jobs:list")

    response = client.post(
        reverse("login"),
        {"username": user.username, "password": PASSWORD, "next": job_list},
    )

    assert response.status_code == 302
    assert response["Location"] == job_list


@pytest.mark.django_db
def test_wrong_password_is_refused(client, user):
    response = client.post(reverse("login"), {"username": user.username, "password": "wrong"})

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_inactive_staff_user_cannot_log_in(client, user):
    user.is_active = False
    user.save()

    client.post(reverse("login"), {"username": user.username, "password": PASSWORD})

    assert "_auth_user_id" not in client.session
