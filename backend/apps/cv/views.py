from django.http import FileResponse, Http404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import CVVersion

from .parsers import extract_text
from .serializers import CVUploadSerializer, CVVersionSerializer


class CVVersionViewSet(viewsets.ModelViewSet):
    serializer_class = CVVersionSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return CVVersion.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        from apps.billing.quotas import check_resource_quota

        current_count = CVVersion.objects.filter(user=request.user).count()
        quota = check_resource_quota(request.user, "max_cv_versions", current_count)
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

        serializer = CVUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from .serializers import _detect_real_filetype

        file = serializer.validated_data["file"]
        name = serializer.validated_data["name"]

        # Use magic-byte detection, not the client-supplied content_type.
        # Map to the MIME strings the parser expects.
        real_type = _detect_real_filetype(file)
        mime_map = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        extracted_text = extract_text(file, mime_map.get(real_type, ""))
        file.seek(0)

        cv = CVVersion.objects.create(
            user=request.user,
            name=name,
            file=file,
            file_size=file.size,
            extracted_text=extracted_text,
        )

        output = CVVersionSerializer(cv)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        cv = self.get_object()
        CVVersion.objects.filter(user=request.user).update(is_default=False)
        cv.is_default = True
        cv.save()
        return Response(CVVersionSerializer(cv).data)


class CVDownloadView(APIView):
    """Owner-scoped CV file download.

    Without this, an attacker who guessed the upload path on the local
    filesystem (or got it from a leaked URL) could download anyone's CV.
    Always serve files through this view in production rather than exposing
    MEDIA_URL directly.
    """

    def get(self, request, pk):
        try:
            cv = CVVersion.objects.get(pk=pk, user=request.user)
        except CVVersion.DoesNotExist as e:
            raise Http404("CV not found") from e

        if not cv.file:
            raise Http404("File missing")

        response = FileResponse(
            cv.file.open("rb"),
            as_attachment=True,
            filename=f"{cv.name}{cv.file.name[-5:] if cv.file.name else ''}",
        )
        return response
