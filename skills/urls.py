from django.urls import path

from . import views

app_name = "skills"

urlpatterns = [
    path("", views.skill_list, name="list"),
    path("new/", views.skill_create, name="create"),
    path("<int:pk>/edit/", views.skill_update, name="update"),
    path("<int:pk>/delete/", views.skill_delete, name="delete"),
]
