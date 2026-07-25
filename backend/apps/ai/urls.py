from django.urls import path

from . import views

urlpatterns = [
    path("ai/providers/", views.ProvidersView.as_view(), name="ai-providers"),
    path("ai/cover-letter/", views.CoverLetterView.as_view(), name="ai-cover-letter"),
    path(
        "ai/cover-letter/stream/<str:task_id>/",
        views.CoverLetterStreamView.as_view(),
        name="ai-cover-letter-stream",
    ),
    path(
        "ai/cover-letters/",
        views.CoverLetterListView.as_view(),
        name="ai-cover-letter-list",
    ),
    path("ai/question-answer/", views.QAView.as_view(), name="ai-qa"),
    path("ai/fit-score/", views.FitScoreView.as_view(), name="ai-fit-score"),
    path("ai/ats-score/", views.ATSScoreView.as_view(), name="ai-ats-score"),
    path("ai/usage/", views.AIUsageView.as_view(), name="ai-usage"),
]
