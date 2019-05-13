from django.core.cache import cache
from django.shortcuts import render

# Create your views here.
from rest_framework.exceptions import APIException, NotFound, AuthenticationFailed
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from DjangoRESTTpp.settings import VIEWER_USER_TIMEOUT
from Viewer.models import ViewerUser
from Viewer.serializers import ViewerUserSerializer
from utils.user_token_util import generrate_viewer_token


class ViewerUserAPIView(CreateAPIView):
    queryset = ViewerUser.objects.all()
    serializer_class = ViewerUserSerializer

    def post(self, request, *args, **kwargs):
        action = request.query_params.get('action')

        if action == 'register':
            return self.create(request, *args, **kwargs)
        elif action == 'login':
            return self.do_login(request, *args, **kwargs)
        else:
            raise APIException(detail='错误的操作')

    def do_login(self,request,*args):
        # data和query_params的区别
        # data 以表单形式提交上来的数据
        # query_params是地址问号后面的参数

        # GET和POST的区别
        # GET：使用场景：动作是获取，下载数据如果用POST虽然能请求成功，但是一定下载不下来
        # POST：使用场景：动作是提交，用来传数据，用GET也可以传数据，可以在后面用？拼接，但是GET有局限性后面的参数不是无限拼接的，很多服务器在接收的时候如果参数过长，就处理不了了，如果服务器没限制，后面的参数如果超过4kb就传不上去了
        # 有说法说POST比GET更安全，错的，一个是直接可见，另一个是需要抓包
        # POST比GET相对安全，可以屏蔽一些小白用户
        # 在开发中，可能经常会用GET请求，再开发中，如果只传3-5个参数或十个，二十个不是非常复杂的参数，GET的速度快于POST，当程序出错的时候，POST想要演示数据，很难，而GET在地址上输入就可以看。
        v_username = request.data.get('v_username')
        v_password = request.data.get('v_password')

        # 根据用户名查询
        users = ViewerUser.objects.filter(v_username=v_username)

        if not users.exists():
            raise NotFound(detail='对象未找到')

        user = users.first()

        if not user.check_password(v_password):
            raise AuthenticationFailed(detail='密码错误')

        token = generrate_viewer_token()

        cache.set(token,user.id,timeout=VIEWER_USER_TIMEOUT)
        data ={
            'msg':'ok',
            'status':HTTP_200_OK,
            'token':token,
        }


        return Response(data)






