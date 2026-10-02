from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated

class SafeMethodsOrStaff(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_staff)

class OwnerOrStaff(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated)
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        vehicle = obj if hasattr(obj, "owner_id") else getattr(obj, "vehicle", None)
        return bool(vehicle and vehicle.owner_id == request.user.id)
