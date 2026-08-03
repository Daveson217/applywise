from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("watchlist", views.WatchlistCompanyViewSet, basename="watchlist")

urlpatterns = [
    path("watchlist/detect-ats/", views.ATSDetectView.as_view(), name="detect-ats"),
    path("watchlist/probe/", views.ATSProbeByNameView.as_view(), name="probe-ats"),
    path("watchlist/matches/", views.MatchedJobsView.as_view(), name="matched-jobs"),
    path(
        "watchlist/matches/<int:pk>/dismiss/",
        views.MatchedJobDismissView.as_view(),
        name="matched-job-dismiss",
    ),
    path("watchlist/recheck/", views.RecheckMatchesView.as_view(), name="recheck-matches"),
    path("watchlist/import/", views.WatchlistImportView.as_view(), name="watchlist-import"),
    path(
        "watchlist/<int:company_pk>/rules/",
        views.WatchlistRuleViewSet.as_view({"get": "list", "post": "create"}),
        name="watchlist-rules-list",
    ),
    path(
        "watchlist/<int:company_pk>/rules/<int:pk>/",
        views.WatchlistRuleViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="watchlist-rules-detail",
    ),
    path(
        "watchlist/<int:company_pk>/postings/",
        views.WatchlistPostingsView.as_view(),
        name="watchlist-postings",
    ),
    path("", include(router.urls)),
]
