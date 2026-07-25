import io
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_obj) -> str:
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


def extract_text_from_docx(file_obj) -> str:
    try:
        from docx import Document

        doc = Document(file_obj)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""


def extract_text(file_obj, content_type: str) -> str:
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_obj)
    elif "wordprocessingml" in content_type:
        return extract_text_from_docx(file_obj)
    return ""
