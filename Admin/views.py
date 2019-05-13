import uuid

from django.core.cache import cache
from django.shortcuts import render

# Create your views here.
from rest_framework.exceptions import APIException
from rest_framework.generics import CreateAPIView, ListCreateAPIView

from Admin.authentication import AdminUserAuthentication
from Admin.models import AdminUser, Permission
from Admin.permissions import SuperAdminUserPermission
from Admin.serializers import AdminUserSerializer, PermissionSerializer
from rest_framework.response import Response

from DjangoRESTTpp.settings import ADMIN_USER_TIMEOUT, ADMIN_USERS
from utils.user_token_util import generrate_admin_token


class AdminUsersAPIView(CreateAPIView):
    serializer_class = AdminUserSerializer
    queryset = AdminUser.objects.filter(is_delete=False)

    def post(self, request, *args, **kwargs):
        action = request.query_params.get('action')

        if action == 'register':
            # 干扰创建过程，在创建过程时将属性修改成超级管理员
            # 创建时，判断用户名是否在超级管理员用户元组中（改元组在settings.py中设置）
            # 重写perform_create()方法
            return self.create(request, *args, **kwargs)

        elif action == 'login':
            a_username = request.data.get('a_username')
            a_password = request.data.get('a_password')
            # print(a_username)
            # print(a_password)     # 未加密
            users = AdminUser.objects.filter(a_username=a_username)

            if not users.exists():
                raise APIException(detail='用户不存在')

            user = users.first()

            if not user.check_admin_password(a_password):
                raise APIException(detail="用户密码错误")

            if user.is_delete:
                raise APIException(detail="用户已离职")

            token = generrate_admin_token()
            # 保存在缓存中
            cache.set(token, user.id, timeout=ADMIN_USER_TIMEOUT)
            data = {
                "msg": "ok",
                "status": 200,
                "token": token,

            }

            return Response(data)
        else:
            raise APIException(detail='请提供正确的动作')

    def perform_create(self, serializer):
        # 判定用户名是否在管理员用户表中
        # 用户名在request中，request在self中
        a_username = self.request.data.get('a_username')
        # 要记得在序列化中添加is_super字段
        serializer.save(is_super=a_username in ADMIN_USERS)

        # if a_username in ADMIN_USERS:
        #     serializer.save(is_super=True)
        # else:
        #     serializer.save()

#
class PermissionsAPIViews(ListCreateAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    # 认证
    authentication_classes = (AdminUserAuthentication, )
    # 检查权限
    permission_classes = (SuperAdminUserPermission,)

    # 差量更新，修改用户权限（有超级管理员用户权限的，才能修改用户权限）
    def patch(self, request, *args, **kwargs):
        # 判断参数：必须有登陆，必须有创建权限，其他用户的标识
        user_id = request.data.get('user_id')
        permission_id = request.data.get('permission_id')

        try:
            permission = Permission.objects.get(pk=permission_id)
        except Exception as e:
            print(e)
            raise APIException(detail="权限不存在")

        try:
            user = AdminUser.objects.get(pk=user_id)
        except Exception as e:
            print(e)
            raise APIException(detail='用户不存在')

        # 给用户user添加permission权限
        user.permission_set.add(permission)
        data = {
            'msg': 'add success',
            'status': 201,
        }


        return Response(data)





