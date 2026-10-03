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
    def serialize_result(self, obj, to_field_name):
        return {"id": str(getattr(obj, to_field_name)), "text": member_label(obj)}


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
