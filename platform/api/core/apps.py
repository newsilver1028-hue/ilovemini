from django.apps import AppConfig
class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "회원·차량·포인트 운영"

    def ready(self):
        from . import phase_one_notifications  # noqa: F401
