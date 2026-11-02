from django.urls import path

from . import views

app_name = "candidates"

urlpatterns = [
    path("", views.CandidateListView.as_view(), name="list"),
    path("new/", views.CandidateCreateView.as_view(), name="create"),
    path("<int:pk>/", views.CandidateDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.CandidateUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.CandidateDeleteView.as_view(), name="delete"),
    path("<int:pk>/status/", views.CandidateStatusView.as_view(), name="status"),
]
