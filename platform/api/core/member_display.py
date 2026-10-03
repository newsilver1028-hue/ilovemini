from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.admin.widgets import AutocompleteSelect
from django.urls import reverse


def member_nickname(user):
    try:
        nickname = user.naver_identity.nickname
    except ObjectDoesNotExist:
        nickname = ""
    return nickname or user.get_full_name() or ("닉네임 미제공" if user.username.startswith("naver_") else user.username)


def member_label(user):
    return f"{member_nickname(user)} / {user.email or '이메일 미제공'} / 회원번호 {user.pk}"


class MemberAutocompleteView(AutocompleteJsonView):
    def get(self, request, *args, **kwargs):
        # Keep this member lookup private and independent of generic FK metadata.
        from django.contrib.auth import get_user_model
        from django.core.paginator import Paginator
        from django.db.models import Q
        from django.http import JsonResponse
        from django.core.exceptions import PermissionDenied
        if not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied
        users = get_user_model().objects.select_related("naver_identity").order_by("-date_joined", "-pk")
        term = request.GET.get("term", "").strip()[:200]
        if term:
            match = Q(username__icontains=term) | Q(email__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(naver_identity__nickname__icontains=term)
            if term.isdecimal() and len(term) <= 18:
                match |= Q(pk=int(term))
            users = users.filter(match)
        page = Paginator(users, 30).get_page(request.GET.get("page", 1))
        return JsonResponse({"results": [{"id": str(user.pk), "text": member_label(user)} for user in page], "pagination": {"more": page.has_next()}})


class MemberAutocompleteSelect(AutocompleteSelect):
    def get_url(self):
        return reverse(f"{self.admin_site.name}:core_partnerstaff_member_autocomplete")

    def optgroups(self, name, value, attrs=None):
        # Use the same readable label for the already-selected account.
        self.choices.field.label_from_instance = member_label
        return super().optgroups(name, value, attrs)


def sync_profile_email(user, profile):
    email = str(profile.get("email") or "").strip()
    if email and user.email != email:
        user.email = email
        user.save(update_fields=["email"])
