from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="list"),
    path("new/", views.job_create, name="create"),
    path("<int:pk>/", views.job_detail, name="detail"),
    path("<int:pk>/edit/", views.job_update, name="update"),
    path("<int:pk>/delete/", views.job_delete, name="delete"),
    path("<int:pk>/toggle-status/", views.job_toggle_status, name="toggle_status"),
]
