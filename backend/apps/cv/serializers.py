from rest_framework import serializers

from apps.applications.models import CVVersion

# Magic-byte signatures for PDF and DOCX (which is a zip file with specific
# internal structure). Client-supplied `content_type` is untrusted — an
# attacker can label anything as application/pdf.
PDF_MAGIC = b"%PDF-"
# DOCX is a ZIP file. All ZIPs start with PK\x03\x04. We additionally check
# the docx-specific [Content_Types].xml shortly after the header.
ZIP_MAGIC = b"PK\x03\x04"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_NAME_LEN = 100


class CVVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVVersion
        fields = [
            "id",
            "name",
            "file",
            "file_size",
            "extracted_text",
            "parsed_json",
            "tags",
            "is_default",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "file_size",
            "extracted_text",
            "parsed_json",
            "created_at",
        ]


def _detect_real_filetype(file_obj) -> str | None:
    """Read the file's magic bytes to verify its true type. Returns
    'pdf', 'docx', or None if it's neither.
    """
    pos = file_obj.tell()
    try:
        file_obj.seek(0)
        head = file_obj.read(2048)
    finally:
        file_obj.seek(pos)

    if head.startswith(PDF_MAGIC):
        return "pdf"
    # Docx is a zip — look for the docx-specific entry name in the central
    # directory. The first 2 KB of a docx almost always includes
    # `word/document.xml` or `[Content_Types].xml`.
    if head.startswith(ZIP_MAGIC) and (b"word/" in head or b"[Content_Types]" in head):
        return "docx"
    return None


class CVUploadSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=MAX_NAME_LEN)
    file = serializers.FileField()

    def validate_name(self, value):
        # Prevent control characters in display names (logs, emails, UI)
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        if any(ord(c) < 32 for c in value):
            raise serializers.ValidationError("Name contains invalid characters.")
        return value

    def validate_file(self, value):
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"File size must be under {MAX_FILE_SIZE // 1024 // 1024} MB."
            )
        if value.size == 0:
            raise serializers.ValidationError("File is empty.")

        # Verify by content, not by client-supplied content_type
        real = _detect_real_filetype(value)
        if real not in ("pdf", "docx"):
            raise serializers.ValidationError("Only PDF and DOCX files are supported.")
        return value
