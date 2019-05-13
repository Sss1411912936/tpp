from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication

# 创建认证器
from Admin.models import AdminUser
from utils.user_token_util import ADMIN


class AdminUserAuthentication(BaseAuthentication):
    # 实现抽象方法
    # 请求相关信息进行用户认证，认证成功返回用户和令牌
    def authenticate(self, request):
        try:
            # 获取token，进行认证
            token = request.query_params.get("token")
            if not token.startswith(ADMIN):
                raise Exception('错误的操作')
            user_id = cache.get(token)
            user = AdminUser.objects.filter(pk=user_id)
            # 返回用户和令牌
            return user, token

        except Exception as e:
            print('认证失败', e)
            return None
