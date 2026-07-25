"""Email sending via Resend (or Django console backend in dev)."""

import html
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def render_template(template: str, context: dict, *, escape_html: bool = False) -> str:
    """Simple {{var}} substitution. Avoids dragging in Django templates.

    When `escape_html=True`, all values are HTML-escaped before substitution.
    Use this for the HTML body of every email — otherwise user-controlled
    fields (company names, posting titles) become XSS vectors in email
    clients that DO render scripts (some webmail clients still do).

    URLs are special-cased: we keep them un-escaped (so href= attributes
    work) but reject any URL not starting with http:// or https:// to
    prevent javascript:/data: URI smuggling.
    """
    rendered = template
    for key, value in context.items():
        str_value = "" if value is None else str(value)
        if escape_html:
            if key.endswith("_url") or key == "url":
                # URL fields: only allow http/https. If the value looks like
                # anything else, replace with a safe placeholder.
                lower = str_value.lower().strip()
                if not (lower.startswith("http://") or lower.startswith("https://")):
                    str_value = "#"
                # Escape any embedded quotes/brackets just in case
                str_value = html.escape(str_value, quote=True)
            else:
                str_value = html.escape(str_value, quote=True)
        rendered = rendered.replace(f"{{{{{key}}}}}", str_value)
    return rendered


JOB_ALERT_TEMPLATE = """Hi {{first_name}},

We found a new job posting matching your watchlist alert for {{company}}:

  {{title}}
  {{location}}

  View the posting: {{url}}

Open Applywise: {{frontend_url}}/watchlist

— Applywise
"""

JOB_ALERT_HTML = """<!DOCTYPE html>
<html><body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 560px; margin: 32px auto; color: #1a1a1a;">
  <h2 style="font-weight: 600; margin: 0 0 16px;">New job at {{company}}</h2>
  <p style="line-height: 1.6;">Hi {{first_name}}, we found a new posting matching your watchlist alert:</p>
  <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 24px 0;">
    <p style="font-weight: 600; font-size: 16px; margin: 0 0 4px;">{{title}}</p>
    <p style="color: #6b7280; margin: 0 0 12px;">{{location}}</p>
    <a href="{{url}}" style="display: inline-block; background: #3B82F6; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: 500;">View posting →</a>
  </div>
  <p style="color: #6b7280; font-size: 14px;">
    <a href="{{frontend_url}}/watchlist" style="color: #3B82F6;">Manage your watchlist on Applywise</a>
  </p>
</body></html>
"""


def send_via_resend(to: str, subject: str, html: str, text: str) -> bool:
    """Send an email through Resend's HTTP API."""
    import requests

    api_key = getattr(settings, "RESEND_API_KEY", "")
    from_email = getattr(settings, "RESEND_FROM_EMAIL", "Applywise <no-reply@applywise.app>")

    if not api_key:
        return False

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_email,
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text,
            },
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Resend API error sending to {to}: {e}")
        return False


def send_email(to: str, subject: str, html: str, text: str) -> bool:
    """Send via Resend if configured; otherwise fall back to Django's email backend.

    In dev, Django's console backend prints the email — useful for verifying
    the pipeline without setting up a real API key.
    """
    if getattr(settings, "RESEND_API_KEY", ""):
        return send_via_resend(to, subject, html, text)

    try:
        send_mail(
            subject=subject,
            message=text,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@applywise.app"),
            recipient_list=[to],
            html_message=html,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to}: {e}")
        return False


def send_job_alert(user, posting) -> bool:
    """Build and send a job alert email for a matched posting."""
    context = {
        "first_name": user.first_name or "there",
        "company": posting.company.name,
        "title": posting.title,
        "location": posting.location or "Remote/Unspecified",
        "url": posting.url,
        "frontend_url": getattr(settings, "FRONTEND_URL", "http://localhost:5173"),
    }

    # Subject must also be cleaned — newlines would let an attacker inject
    # arbitrary email headers.
    raw_subject = f"New role at {posting.company.name}: {posting.title}"
    subject = raw_subject.replace("\n", " ").replace("\r", " ")[:200]

    text = render_template(JOB_ALERT_TEMPLATE, context)  # plain text — no escape
    html_body = render_template(JOB_ALERT_HTML, context, escape_html=True)

    return send_email(user.email, subject, html_body, text)
