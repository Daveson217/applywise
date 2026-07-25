from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("contacts", views.ContactViewSet, basename="contact")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "contacts/<int:contact_pk>/interactions/",
        views.InteractionViewSet.as_view({"get": "list", "post": "create"}),
        name="interaction-list",
    ),
    path(
        "contacts/<int:contact_pk>/interactions/<int:pk>/",
        views.InteractionViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="interaction-detail",
    ),
]
