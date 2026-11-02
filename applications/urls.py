from django.urls import path

from . import views

app_name = "applications"

urlpatterns = [
    path("new/from-job/<int:job_pk>/", views.RecordFromJobView.as_view(), name="record_from_job"),
    path(
        "new/from-candidate/<int:candidate_pk>/",
        views.RecordFromCandidateView.as_view(),
        name="record_from_candidate",
    ),
    path("<int:pk>/move/", views.MoveStageView.as_view(), name="move"),
]
