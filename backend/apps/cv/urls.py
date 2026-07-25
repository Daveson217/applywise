from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("cv", views.CVVersionViewSet, basename="cv")

urlpatterns = [
    path(
        "cv/<int:pk>/download/",
        views.CVDownloadView.as_view(),
        name="cv-download",
    ),
    path("", include(router.urls)),
]
