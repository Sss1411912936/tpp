from rest_framework.permissions import BasePermission

from Admin.models import AdminUser


# 权限创建认证
class SuperAdminUserPermission(BasePermission):

    SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']

    # 实现has_permission
    def has_permission(self, request, view):
        if request.method not in self.SAFE_METHODS:
            users = request.user
            for user in users:
                print(isinstance(user, AdminUser))

            # if isinstance(user,AdminUser) and user.is_super:
            #     return True
            # return False

            # 优化
                return isinstance(user, AdminUser) and user.is_super
        return True