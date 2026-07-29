from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("sfnom/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.applications.urls")),
    path("api/", include("apps.watchlist.urls")),
    path("api/", include("apps.cv.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.ai.urls")),
    path("api/", include("apps.billing.urls")),
    path("api/", include("apps.networking.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
