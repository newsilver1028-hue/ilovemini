from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from .models import AppReviewAccount


class AppReviewAccountAdminForm(forms.ModelForm):
    new_password = forms.CharField(
        label="심사용 비밀번호",
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="최소 12자. 저장 후에는 다시 볼 수 없으며, 변경할 때 새 비밀번호를 입력하세요.",
    )

    class Meta:
        model = AppReviewAccount
        fields = ("username", "is_active")

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password", "")
        if not self.instance.pk and len(password) < 12:
            raise forms.ValidationError("처음 등록할 때는 12자 이상의 비밀번호가 필요합니다.")
        if password and len(password) < 12:
            raise forms.ValidationError("비밀번호는 12자 이상 입력해 주세요.")
        return password

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if username.startswith("naver_"):
            raise forms.ValidationError("네이버 로그인 계정과 구분되는 아이디를 사용해 주세요.")
        User = get_user_model()
        matches = User.objects.filter(username=username)
        if self.instance.user_id:
            matches = matches.exclude(pk=self.instance.user_id)
        if matches.exists():
            raise forms.ValidationError("이미 사용 중인 회원 아이디입니다.")
        return username


@admin.register(AppReviewAccount)
class AppReviewAccountAdmin(admin.ModelAdmin):
    form = AppReviewAccountAdminForm
    list_display = ("username", "is_active", "linked_member", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("username", "user__username")
    fields = ("username", "new_password", "is_active", "user", "created_at", "updated_at")
    readonly_fields = ("user", "created_at", "updated_at")
    ordering = ("-created_at", "username")

    @admin.display(description="앱 회원 계정")
    def linked_member(self, obj):
        return obj.user_id or "첫 로그인 시 생성"

    def has_module_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        password = form.cleaned_data.get("new_password", "")
        if password:
            obj.password_hash = make_password(password)
        super().save_model(request, obj, form, change)
        User = get_user_model()
        if obj.user_id is None:
            member = User.objects.create_user(
                username=obj.username, password=None, first_name="앱 심사 데모",
                is_active=obj.is_active, is_staff=False, is_superuser=False,
            )
            obj.user = member
            obj.save(update_fields=["user", "updated_at"])
        else:
            member = obj.user
            member.is_active = obj.is_active
            member.is_staff = False
            member.is_superuser = False
            member.save(update_fields=["is_active", "is_staff", "is_superuser"])

