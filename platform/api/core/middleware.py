from django.http import HttpResponseBadRequest


class PartnerAdminSecurityHeadersMiddleware:
    """Apply a focused browser policy to the separate partner-admin host."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        invalid_year = False
        if request.path.startswith(("/admin/", "/partner-admin/")):
            for key, value in request.GET.items():
                if key.endswith("__year") or key == "calendar_year":
                    try:
                        invalid_year = not 1900 <= int(value) <= 2100
                    except (TypeError, ValueError):
                        invalid_year = True
                    if invalid_year:
                        break
        response = (HttpResponseBadRequest("조회 연도는 1900~2100년 범위에서 선택해 주세요.")
                    if invalid_year else self.get_response(request))
        if request.get_host().split(":", 1)[0].lower() == "admin.ilovemini.co.kr":
            response.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "font-src 'self' data:; connect-src 'self' https: wss:; "
                "frame-src 'self'; frame-ancestors 'none'; object-src 'none'; "
                "base-uri 'self'; form-action 'self' https://nid.naver.com; "
                "upgrade-insecure-requests",
            )
            response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response
