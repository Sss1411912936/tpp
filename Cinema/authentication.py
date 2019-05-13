from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication

from Cinema.models import CinemaUser
from utils.user_token_util import CINEMA


class CinemaUserAuthentication(BaseAuthentication):
    # 实现认证方法，认证成功，返回用户和令牌，认证失败None
    def authenticate(self, request):
        try:
            token = request.query_params.get('token')
            print('-----------------------------')
            print(token)
            if not token.startswith(CINEMA):
                raise Exception('Cinema认证失败')
            user_id = cache.get(token)
            user = CinemaUser.objects.get(pk=user_id)
            print(cache.get(token))
            return user, token
        except Exception as e:
            print(e, '认证失败')
            return None

