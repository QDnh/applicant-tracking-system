import pytest

PASSWORD = "pw-12345!"


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="staff", password=PASSWORD)


@pytest.fixture
def logged_in_client(client, user):
    """The same object as the `client` fixture, logged in as `user`.

    Requesting both in one test does not give a separate anonymous client; call
    `logged_in_client.logout()` to test anonymous access.
    """
    client.force_login(user)
    return client
