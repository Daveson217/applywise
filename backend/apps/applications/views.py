import csv
import io
import json
from datetime import datetime, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from rest_framework import generics, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import ApplicationFilter
from .models import Application, ApplicationActivity, Tag
from .serializers import (
    ApplicationActivitySerializer,
    ApplicationCreateUpdateSerializer,
    ApplicationDetailSerializer,
    ApplicationListSerializer,
    TagSerializer,
)


class ApplicationViewSet(viewsets.ModelViewSet):
    filterset_class = ApplicationFilter
    search_fields = ["company", "role", "location", "notes"]
    ordering_fields = [
        "created_at",
        "updated_at",
        "applied_date",
        "deadline",
        "company",
        "priority",
    ]
    ordering = ["-updated_at"]

    def get_queryset(self):
        return (
            Application.objects.filter(user=self.request.user)
            .prefetch_related("tags")
            .select_related("cv_version")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ApplicationListSerializer
        if self.action == "retrieve":
            return ApplicationDetailSerializer
        return ApplicationCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        from apps.billing.quotas import check_resource_quota

        current_count = Application.objects.filter(user=request.user).count()
        quota = check_resource_quota(request.user, "max_applications", current_count)
        if not quota.allowed:
            return Response(
                {
                    "error": quota.reason,
                    "limit": quota.limit,
                    "used": quota.used,
                    "plan": quota.plan,
                    "upgrade_url": "/pricing",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)


class ApplicationActivityView(generics.ListAPIView):
    serializer_class = ApplicationActivitySerializer

    def get_queryset(self):
        return ApplicationActivity.objects.filter(
            application_id=self.kwargs["pk"],
            application__user=self.request.user,
        )


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)


class BulkActionView(APIView):
    """Perform bulk operations on multiple applications.

    Body: {action: "status_change"|"delete", ids: [1,2], status?: "applied"}
    """

    # Hard cap to prevent a single request from holding DB locks too long
    MAX_BULK_IDS = 500

    # Whitelist of valid status values — defense in depth even though the
    # model's choices validator would catch this on save.
    _VALID_STATUSES = {
        s
        for s, _ in __import__(
            "apps.applications.models", fromlist=["STATUS_CHOICES"]
        ).STATUS_CHOICES
    }

    def post(self, request):
        from django.db import transaction

        action = request.data.get("action")
        ids = request.data.get("ids", [])

        if not isinstance(ids, list) or not ids:
            return Response(
                {"error": "ids must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(ids) > self.MAX_BULK_IDS:
            return Response(
                {"error": f"Cannot act on more than {self.MAX_BULK_IDS} items at once"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        # Coerce to ints — reject anything else to avoid SQL surprises
        try:
            ids = [int(i) for i in ids]
        except (TypeError, ValueError):
            return Response(
                {"error": "ids must be integers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # User-scoped queryset → an attacker passing IDs they don't own gets
        # a no-op, not unauthorized access to others' rows.
        qs = Application.objects.filter(user=request.user, id__in=ids)

        if action == "status_change":
            new_status = request.data.get("status")
            if new_status not in self._VALID_STATUSES:
                return Response(
                    {"error": "Invalid status value"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            updated = 0
            # Wrap in transaction so a mid-loop failure doesn't leave half-applied state
            with transaction.atomic():
                for app in qs:
                    if app.status != new_status:
                        app.status = new_status
                        app.save()
                        updated += 1
            return Response({"updated": updated})

        if action == "delete":
            with transaction.atomic():
                count, _ = qs.delete()
            return Response({"deleted": count})

        return Response(
            {"error": "Unknown action"},  # don't echo user input back
            status=status.HTTP_400_BAD_REQUEST,
        )


CSV_HEADERS = [
    "company",
    "role",
    "job_type",
    "status",
    "priority",
    "applied_date",
    "deadline",
    "location",
    "is_remote",
    "url",
    "source",
    "salary_min",
    "salary_max",
    "salary_currency",
    "notes",
    "recruiter_name",
    "recruiter_email",
]


class ImportCSVView(APIView):
    """Import applications from a CSV file.

    First call (preview): POST with CSV file → returns parsed rows + detected mapping.
    Second call (commit): POST with {rows: [...]} → creates Application records.
    """

    parser_classes = [MultiPartParser, FormParser]

    # Hard caps to prevent DoS via large CSVs
    MAX_COMMIT_ROWS = 500

    def post(self, request):
        # Commit path
        if request.data.get("commit") == "true" and request.data.get("rows"):
            try:
                rows = json.loads(request.data["rows"])
            except (json.JSONDecodeError, TypeError):
                return Response(
                    {"error": "Invalid rows JSON"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not isinstance(rows, list):
                return Response(
                    {"error": "rows must be a list"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if len(rows) > self.MAX_COMMIT_ROWS:
                return Response(
                    {"error": (f"Cannot import more than {self.MAX_COMMIT_ROWS} rows at once")},
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )

            from apps.billing.quotas import check_resource_quota

            created = 0
            skipped_over_limit = 0

            for row in rows:
                cleaned = {k: v for k, v in row.items() if k in CSV_HEADERS and v not in (None, "")}
                if not cleaned.get("company") or not cleaned.get("role"):
                    continue
                cleaned.setdefault("job_type", "fulltime")
                cleaned.setdefault("status", "saved")
                cleaned.setdefault("priority", "medium")
                if "is_remote" in cleaned:
                    cleaned["is_remote"] = str(cleaned["is_remote"]).lower() in (
                        "true",
                        "yes",
                        "1",
                    )
                for f in ("salary_min", "salary_max"):
                    if f in cleaned:
                        try:
                            cleaned[f] = int(cleaned[f])
                        except (ValueError, TypeError):
                            del cleaned[f]

                # Enforce per-row so a CSV can't blow past the cap
                current = Application.objects.filter(user=request.user).count()
                quota = check_resource_quota(request.user, "max_applications", current)
                if not quota.allowed:
                    skipped_over_limit = len(rows) - created
                    break

                try:
                    Application.objects.create(user=request.user, **cleaned)
                    created += 1
                except Exception:
                    continue

            response = {"created": created}
            if skipped_over_limit:
                response["skipped_over_limit"] = skipped_over_limit
                response["message"] = (
                    f"Hit your plan limit after creating {created} applications. "
                    f"Upgrade to import the rest."
                )
            return Response(response)

        # Preview path
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file uploaded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cap size BEFORE reading into memory to prevent OOM-DoS.
        # 2 MB is plenty for tens of thousands of typical job-app rows.
        MAX_CSV_SIZE = 2 * 1024 * 1024
        if file.size and file.size > MAX_CSV_SIZE:
            return Response(
                {"error": f"CSV exceeds {MAX_CSV_SIZE // 1024 // 1024} MB limit"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        try:
            text = file.read(MAX_CSV_SIZE + 1).decode("utf-8")
        except UnicodeDecodeError:
            return Response(
                {"error": "File must be UTF-8 encoded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(text.encode("utf-8")) > MAX_CSV_SIZE:
            return Response(
                {"error": "CSV exceeds size limit"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)[:100]  # cap preview at 100 rows

        return Response(
            {
                "headers": reader.fieldnames or [],
                "rows": rows,
                "row_count": len(rows),
            }
        )


class ExportView(APIView):
    """Export applications as CSV or JSON. Gated by Pro+ subscription
    (unless PAYMENTS_ENABLED is False, in which case everyone can export)."""

    def get(self, request):
        from apps.billing.quotas import payments_enabled

        if payments_enabled():
            # Inline permission check (avoids circular import)
            try:
                sub = request.user.subscription
                if sub.plan not in ("pro", "premium"):
                    return Response(
                        {"error": "Export requires a Pro or Premium subscription."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            except Exception:
                return Response(
                    {"error": "Export requires a Pro or Premium subscription."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Use `type` rather than `format` because DRF reserves `format` for
        # renderer negotiation and would 404 on unknown values.
        fmt = (
            request.query_params.get("type") or request.query_params.get("export") or "csv"
        ).lower()
        apps_qs = Application.objects.filter(user=request.user)

        if fmt == "json":
            data = list(
                apps_qs.values(
                    "company",
                    "role",
                    "status",
                    "job_type",
                    "priority",
                    "applied_date",
                    "deadline",
                    "location",
                    "is_remote",
                    "url",
                    "source",
                    "salary_min",
                    "salary_max",
                    "salary_currency",
                    "notes",
                    "recruiter_name",
                    "recruiter_email",
                    "created_at",
                )
            )
            response = HttpResponse(
                json.dumps(data, default=str, indent=2),
                content_type="application/json",
            )
            response["Content-Disposition"] = 'attachment; filename="applywise-applications.json"'
            return response

        # CSV (default).
        # SECURITY: Excel/LibreOffice/Numbers treat cells starting with
        # = + - @ TAB CR as formulas — including =CMD()|... that can run
        # arbitrary commands when the recipient opens the file. We prefix
        # any such cell with a single quote to neutralize it. This is
        # OWASP-recommended "CSV injection" defense.
        def _safe(value):
            s = "" if value is None else str(value)
            if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
                return "'" + s
            return s

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="applywise-applications.csv"'
        writer = csv.DictWriter(response, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for app in apps_qs:
            writer.writerow({h: _safe(getattr(app, h, "")) for h in CSV_HEADERS})
        return response


class DailyCountsView(APIView):
    """Daily application creation counts for the activity heatmap."""

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 365))
        except ValueError:
            days = 365
        days = min(max(days, 1), 730)

        since = datetime.now().date() - timedelta(days=days)

        counts = (
            Application.objects.filter(user=request.user, created_at__date__gte=since)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        return Response([{"date": str(c["date"]), "count": c["count"]} for c in counts])
