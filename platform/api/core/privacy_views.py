import os

from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def privacy_policy(request):
    return render(
        request,
        "public/privacy_policy.html",
        {
            "controller_name": os.getenv("PRIVACY_SERVICE_NAME", "아이러브미니"),
            "legal_entity_name": os.getenv("PRIVACY_LEGAL_ENTITY_NAME", "유엠(um)"),
            "business_registration_number": os.getenv(
                "PRIVACY_BUSINESS_REGISTRATION_NUMBER", "120-11-92135"
            ),
            "privacy_contact_phone": os.getenv(
                "PRIVACY_CONTACT_PHONE", "0507-1416-5035"
            ),
            "effective_date": os.getenv("PRIVACY_POLICY_EFFECTIVE_DATE", "2026년 10월 20일"),
        },
    )


@require_GET
def terms_of_service(request):
    return render(request, "public/terms_of_service.html")
