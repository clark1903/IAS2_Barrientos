from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AuditLog, Profile

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "profile"
    fk_name = "user"
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_select_related = ("user",)
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "model_name", "object_pk", "actor", "ip_address")
    list_filter = ("action", "model_name", "created_at")
    search_fields = ("object_pk", "actor__username", "actor__email", "record_hash")
    readonly_fields = (
        "created_at",
        "action",
        "model_name",
        "object_pk",
        "actor",
        "ip_address",
        "before_state",
        "after_state",
        "record_hash",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UserAdmin(DjangoUserAdmin):
    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        return [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
