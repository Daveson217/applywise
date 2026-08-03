import json

from rest_framework import generics, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.table_parser import (
    ImportParseError,
    parse_upload,
    pick,
)
from ats_adapters.registry import detect_ats_from_url

from .models import JobPosting, WatchlistCompany, WatchlistRule
from .serializers import (
    ATSDetectSerializer,
    JobPostingSerializer,
    MatchedJobSerializer,
    WatchlistCompanyCreateSerializer,
    WatchlistCompanySerializer,
    WatchlistRuleSerializer,
)


def _detect_and_apply_ats(company, *, force: bool = False):
    """Best-effort: try URL-based detection first, then name-based probe.
    Silently no-op if neither works — the row just stays unscheduled.
    Called on create and on update; safe to call repeatedly.

    `force=True` re-runs detection even if the company already has an ATS
    set. Use on edit so a URL change from Greenhouse → Lever (or a fix to a
    bad slug) is picked up.
    """
    if company.ats_provider and not force:
        return

    # 1) URL-based (fast, no HTTP).
    if company.careers_url:
        result = detect_ats_from_url(company.careers_url)
        if result:
            company.ats_provider = result[0]
            company.ats_company_slug = result[1]
            company.save(update_fields=["ats_provider", "ats_company_slug"])
            return

    # 2) Name-based probe (a few HTTP calls, bounded).
    from .probe import probe_by_name

    probed = probe_by_name(company.name)
    if probed:
        company.ats_provider = probed.provider
        company.ats_company_slug = probed.slug
        # Fill in the canonical URL if we didn't have one.
        update_fields = ["ats_provider", "ats_company_slug"]
        if not company.careers_url:
            company.careers_url = probed.board_url
            update_fields.append("careers_url")
        company.save(update_fields=update_fields)
    elif force:
        # Re-detection asked but nothing matched — clear stale ATS data so
        # the "Not scraping" badge shows and the user isn't misled.
        if company.ats_provider or company.ats_company_slug:
            company.ats_provider = ""
            company.ats_company_slug = ""
            company.save(update_fields=["ats_provider", "ats_company_slug"])


class WatchlistCompanyViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistCompanySerializer
    search_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        return WatchlistCompany.objects.filter(user=self.request.user).prefetch_related(
            "rules", "postings"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return WatchlistCompanyCreateSerializer
        return WatchlistCompanySerializer

    def create(self, request, *args, **kwargs):
        from apps.billing.quotas import check_resource_quota

        current_count = WatchlistCompany.objects.filter(user=request.user).count()
        quota = check_resource_quota(request.user, "max_watchlist", current_count)
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

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()

        _detect_and_apply_ats(company)

        output_serializer = WatchlistCompanySerializer(company, context={"request": request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        # Re-run ATS detection unconditionally on edit — the user may have
        # changed the URL to a different provider or fixed a bad slug.
        company = serializer.save()
        _detect_and_apply_ats(company, force=True)


class WatchlistRuleViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistRuleSerializer

    def get_queryset(self):
        return WatchlistRule.objects.filter(
            company_id=self.kwargs["company_pk"],
            company__user=self.request.user,
        )

    def perform_create(self, serializer):
        company = WatchlistCompany.objects.get(pk=self.kwargs["company_pk"], user=self.request.user)
        serializer.save(company=company)


class WatchlistPostingsView(generics.ListAPIView):
    serializer_class = JobPostingSerializer

    def get_queryset(self):
        return JobPosting.objects.filter(
            company_id=self.kwargs["company_pk"],
            company__user=self.request.user,
        )


class MatchedJobsView(generics.ListAPIView):
    """The Matched Jobs feed: postings that passed the user's filters, across
    all their companies. Excludes dismissed rows. Ordered by relevance then
    recency."""

    serializer_class = MatchedJobSerializer

    def get_queryset(self):
        return (
            JobPosting.objects.filter(
                company__user=self.request.user,
                matched_rules=True,
                match_dismissed=False,
                is_active=True,
            )
            .select_related("company")
            .order_by("-ai_relevance_score", "-matched_at")
        )


class MatchedJobDismissView(APIView):
    """Dismiss (hide) a matched job from the feed."""

    def post(self, request, pk):
        try:
            posting = JobPosting.objects.get(pk=pk, company__user=request.user)
        except JobPosting.DoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )
        posting.match_dismissed = True
        posting.save(update_fields=["match_dismissed"])
        return Response({"dismissed": True})


class RecheckMatchesView(APIView):
    """Re-run matching over all existing active postings for the user's
    companies. Use after changing filters so already-seen jobs get
    re-evaluated (normal monitoring only checks newly-scraped postings)."""

    def post(self, request):
        from .tasks import _check_rules

        companies = WatchlistCompany.objects.filter(user=request.user).prefetch_related("rules")
        checked = 0
        for company in companies:
            postings = JobPosting.objects.filter(
                company=company, is_active=True, match_dismissed=False
            )
            for posting in postings:
                # Reset match state so filters can newly reject previously-matched rows.
                posting.matched_rules = False
                posting.matched_at = None
                posting.save(update_fields=["matched_rules", "matched_at"])
                _check_rules(posting, company)
                checked += 1
        return Response({"rechecked": checked})


class ATSDetectView(APIView):
    def post(self, request):
        serializer = ATSDetectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data["url"]

        result = detect_ats_from_url(url)
        if result:
            return Response({"detected": True, "provider": result[0], "slug": result[1]})
        return Response({"detected": False, "provider": None, "slug": None})


class ATSProbeByNameView(APIView):
    """Try to auto-detect a company's ATS by slugifying the name and probing
    each known provider's public API. Best-effort fallback for when the user
    doesn't have an ATS-recognizable URL."""

    def post(self, request):
        name = str(request.data.get("name") or "").strip()
        if not name or len(name) > 200:
            return Response(
                {"error": "name is required (2-200 chars)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .probe import probe_by_name

        result = probe_by_name(name)
        if result:
            return Response(
                {
                    "detected": True,
                    "provider": result.provider,
                    "slug": result.slug,
                    "board_url": result.board_url,
                }
            )
        return Response({"detected": False})


# Header aliases we accept for the two watchlist columns. Users' CSVs are
# messy — Handshake exports, LinkedIn saves, hand-typed sheets all differ.
_NAME_ALIASES = ("name", "company", "company_name", "employer", "organization")
_URL_ALIASES = (
    "careers_url",
    "careers_page_url",
    "careers_page",
    "careers",
    "url",
    "career_url",
    "career_page",
    "jobs_page",
    "jobs_url",
    "website",
)


class WatchlistImportView(APIView):
    """Two-phase watchlist import from CSV or XLSX.

    Preview (multipart, no `commit`): parse and return normalized rows so the
    user can eyeball them before committing.

    Commit (`commit=true` + `rows` JSON): create WatchlistCompany rows,
    auto-detect ATS provider from the careers URL if present, enforce the
    tier's max_watchlist quota per row.
    """

    parser_classes = [MultiPartParser, FormParser]

    MAX_COMMIT_ROWS = 500
    MAX_PREVIEW_ROWS = 100

    def post(self, request):
        # ── Commit path ────────────────────────────────────────────
        if request.data.get("commit") == "true" and request.data.get("rows"):
            return self._commit(request)

        # ── Preview path ───────────────────────────────────────────
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file uploaded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            headers, rows = parse_upload(file, filename=file.name)
        except ImportParseError as e:
            return Response(
                {"error": str(e)},
                status=(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                    if "size" in str(e).lower()
                    else status.HTTP_400_BAD_REQUEST
                ),
            )

        # Normalize into {name, careers_url} shape — drop obviously blank rows
        normalized = []
        for row in rows[: self.MAX_PREVIEW_ROWS]:
            name = pick(row, *_NAME_ALIASES)
            url = pick(row, *_URL_ALIASES)
            if not name:
                # Skip rows without a name — they can't produce a watchlist entry
                continue
            normalized.append({"name": name[:255], "careers_url": url[:500]})

        if not normalized:
            return Response(
                {
                    "error": (
                        "No usable rows found. Ensure your file has a 'name' or 'company' column."
                    ),
                    "detected_headers": headers,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "headers": ["name", "careers_url"],
                "detected_headers": headers,
                "rows": normalized,
                "row_count": len(normalized),
            }
        )

    def _commit(self, request):
        from apps.billing.quotas import check_resource_quota

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
                {"error": f"Cannot import more than {self.MAX_COMMIT_ROWS} rows at once"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # Existing names for this user — de-dupe so the import is idempotent.
        # Case-insensitive so "Stripe" and "stripe" collapse.
        existing = {
            n.lower()
            for n in WatchlistCompany.objects.filter(user=request.user).values_list(
                "name", flat=True
            )
        }

        created = 0
        skipped_duplicates = 0
        skipped_over_limit = 0

        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()[:255]
            careers_url = str(row.get("careers_url") or "").strip()[:500]
            if not name:
                continue
            if name.lower() in existing:
                skipped_duplicates += 1
                continue

            current = WatchlistCompany.objects.filter(user=request.user).count()
            quota = check_resource_quota(request.user, "max_watchlist", current)
            if not quota.allowed:
                skipped_over_limit = len(rows) - created - skipped_duplicates
                break

            company = WatchlistCompany.objects.create(
                user=request.user,
                name=name,
                careers_url=careers_url,
            )
            existing.add(name.lower())

            # ATS auto-detection is regex-only (no HTTP) — safe to run inline.
            if company.careers_url:
                result = detect_ats_from_url(company.careers_url)
                if result:
                    company.ats_provider = result[0]
                    company.ats_company_slug = result[1]
                    company.save(update_fields=["ats_provider", "ats_company_slug"])

            created += 1

        response = {
            "created": created,
            "skipped_duplicates": skipped_duplicates,
        }
        if skipped_over_limit:
            response["skipped_over_limit"] = skipped_over_limit
            response["message"] = (
                f"Hit your plan limit after creating {created} companies. "
                f"Upgrade to import the rest."
            )
        return Response(response)
