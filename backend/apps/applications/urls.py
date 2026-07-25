from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("applications", views.ApplicationViewSet, basename="application")
router.register("tags", views.TagViewSet, basename="tag")

urlpatterns = [
    path(
        "applications/bulk-action/",
        views.BulkActionView.as_view(),
        name="application-bulk-action",
    ),
    path(
        "applications/import-csv/",
        views.ImportCSVView.as_view(),
        name="application-import-csv",
    ),
    path(
        "applications/export/",
        views.ExportView.as_view(),
        name="application-export",
    ),
    path(
        "applications/daily-counts/",
        views.DailyCountsView.as_view(),
        name="application-daily-counts",
    ),
    path(
        "applications/<int:pk>/activity/",
        views.ApplicationActivityView.as_view(),
        name="application-activity",
    ),
    path("", include(router.urls)),
]
