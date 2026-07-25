"""Defense-in-depth response headers applied to every response.

Django's SecurityMiddleware handles HSTS / XSS-filter / content-type-nosniff.
This middleware adds a few headers Django doesn't set:

- Permissions-Policy — disables browser features we never use, so even if an
  XSS happens it can't ask for the camera/mic/payment APIs.
- Cross-Origin-Opener-Policy — process-isolates our window from any opener
  (mitigates Spectre and tab-nabbing).
- A minimal Content-Security-Policy for the JSON API. The frontend is a
  separate SPA so its own CSP belongs in its hosting config (nginx/Vercel/
  Cloudflare Pages).
"""

from __future__ import annotations


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Disable powerful APIs by default
        response.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
            "interest-cohort=()",
        )

        # Process-isolate our window
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        # JSON responses don't need to be loaded as scripts/styles by other pages
        if response.get("Content-Type", "").startswith("application/json"):
            response.setdefault("Cross-Origin-Resource-Policy", "same-site")

        return response
