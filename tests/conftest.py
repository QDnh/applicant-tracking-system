import pytest

PASSWORD = "pw-12345!"


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="staff", password=PASSWORD)


@pytest.fixture
def logged_in_client(client, user):
    client.force_login(user)
    return client
