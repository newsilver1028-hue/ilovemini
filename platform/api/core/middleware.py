class PartnerAdminSecurityHeadersMiddleware:
    """Apply a focused browser policy to the separate partner-admin host."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
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
