from rest_framework.permissions import BasePermission
class AdminOnlyAPI(BasePermission):
    message='This API is restricted to authorized administrators.'
    def has_permission(self,request,view): return bool(request.user and request.user.is_authenticated and request.user.is_staff)
