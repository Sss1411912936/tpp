import uuid

from alipay import AliPay
from django.core.cache import cache
from django.db.models import Q
import datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view

from rest_framework.exceptions import APIException
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from Admin.authentication import AdminUserAuthentication
from Cinema.authentication import CinemaUserAuthentication
from Cinema.models import CinemaUser, CinemaMovieOrder, Cinema, Hall, PaiDang, ORDER_PAY
from Cinema.permissions import AdminUserPermission, CinemaMovieOrderPermission, CinemaPermission
from Cinema.srializers import CinemaUserSerializer, CinemaMovieOrderSerializer, CinemaSerializer, HallSerializer, \
    PaiDangSerializer
from Common.models import Movie
from DjangoRESTTpp.settings import CINEMA_USER_TIMEOUT, ALIPAY_PUBLIC_KEY, APP_PRIVATE_KEY
from utils.user_token_util import generrate_cinema_token


class CinemaUsersAPIView(ListCreateAPIView):
    queryset = CinemaUser.objects.all()
    serializer_class = CinemaUserSerializer
    # 超级管理员权限可以看到所有的影院用户
    # 添加认证器，认证超级管理员
    authentication_classes = (AdminUserAuthentication,)
    permission_classes = (AdminUserPermission,)

    def post(self, request, *args, **kwargs):
        action = request.query_params.get('action')

        if action == 'register':
            return self.create(request, *args, **kwargs)
        elif action == 'login':
            return self.do_login(request, *args, **kwargs)
        else:
            raise APIException(detail='请提供正确操作')

    def do_login(self, request, *args, **kwargs):
        c_username = request.data.get('c_username')
        c_password = request.data.get('c_password')

        users = CinemaUser.objects.filter(c_username=c_username)

        if not users.exists():
            raise APIException(detail='用户不存在')
        user = users.first()

        if not user.check_user_password(c_password):
            raise APIException(detail='密码错误')

        if user.is_delete:
            raise APIException(detail='用户已删除')

        token = generrate_cinema_token()
        print('dsgfhjl_____________' + str(user.id))

        # 影院用户、后台管理用户都可登陆，tocken值不重复
        # uuid保证在同一时空中不会重复
        # 在cache中key不一样，但是值有可能重复，id都从1开始
        # 登陆的是影院用户，拿着影院用户的token去请求后台管理，有可能会成功，因为验证得是token
        cache.set(token, user.id, timeout=CINEMA_USER_TIMEOUT)

        data = {
            'msg': 'ok',
            'status': 200,
            'token': token,
        }

        return Response(data)


class CinemaMovieOrdersAPIView(ListCreateAPIView):
    queryset = CinemaMovieOrder.objects.all()
    serializer_class = CinemaMovieOrderSerializer
    # 有权限问题：获取应该影院用户端、超级管理员都可以获取，创建应该由影院用户创建

    # 订单生成：post登陆（需要用户登陆）
    # 1、认证器：需要cinemauser的认证,AdminUser也可以
    authentication_classes = (CinemaUserAuthentication, AdminUserAuthentication)
    # 2、如果认证失败，就没有权限
    permission_classes = (CinemaMovieOrderPermission,)

    # 管理员用户能看到所有影院的；影院用户只能看到自己的
    # 因此要判断用户身份，根据身份，返回不同数据
    # 即修改返回数据。要重写get方法（进ListCreateAPIView，找到get()，get里面什么都没有，只是调用了list，进list，list里面有分页……，调用了get_queryset(),因此可以重写get_queryset()，get_queryset()是GenericAPIView里面的）
    # 重写get_queryset
    def get_queryset(self):
        # 调用父类中的queryset
        queryset = super(CinemaMovieOrdersAPIView, self).get_queryset()

        # 创建电影：需要认证、需要权限
        # 做判断：
        # 如果user是影院用户：则查自己的c_userid_id=user.id
        user = self.request.user
        if isinstance(user, CinemaUser):
            queryset = queryset.filter(c_user_id=user.id)
        # 如果是管理员用户，则返回所有数据
        return queryset

    def post(self, request, *args, **kwargs):
        user = self.request.user
        user_id = user.id
        movie_id = request.data.get('c_movie_id')
        movie = Movie.objects.get(pk=movie_id)
        c_price = movie.m_price  # 验证是在post之后认证的，进ListCreateAPIView，在post里面进行create，在create里面进行验证

        # 修改创建过程
        # 前端只需要传movie_id，剩下的c_price,user_id,
        print(request.data)  # <QueryDict: {'c_movie_id': ['1']}>        # 实验发现QueryDict不可变
        print(type(request.data))  # <class 'django.http.request.QueryDict'>

        # request.data.update({'c_price': c_price, 'c_user_id': user_id})     # 报错，QueryDict不可变

        # 可对request.data进行重新赋值，request修行不推荐修改

        # 可以自己拿数据，构成字典，实现创建create
        request_data = {'c_price': c_price, 'c_user_id': user_id, 'c_movie_id': movie_id}

        # 如果电影已经买过了，不需要再买第二次：
        orders = CinemaMovieOrder.objects.filter(c_movie_id=movie_id).filter(c_user_id=user_id)
        if orders.exists():
            raise APIException(detail='已购买')

        # 将create内容复制进来，在ListCreateAPIView中的post返回的create里
        # data=request.data改成data=request_data
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        print(serializer)
        '''
        CinemaMovieOrderSerializer(context={'request': <rest_framework.request.Request object>, 'format': None, 'view': <Cinema.views.CinemaMovieOrdersAPIView object>}, data={'c_price': 0, 'c_user_id': 1, 'c_movie_id': '1'}):
        c_user_id = ReadOnlyField()      # 只读字段不能修改
        c_movie_id = ReadOnlyField()
        c_status = IntegerField(max_value=2147483647, min_value=-2147483648, required=False)
        c_price = FloatField(required=False)    
        '''
        # self.perform_create(serializer)
        # 改写self.perform_create(serializer)
        # 外间关联字段是只读字段，是不可修改的，想修改值，要自己传输验证后的字段
        serializer.save(c_price=c_price, c_user_id=user_id, c_movie_id=movie_id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)
        # 复制完毕


# 订单付款是修改订单状态，可以认为是订单的post，改订单状态
# 订单能够看，能够删（逻辑删除），不能修改
class CinemaMovieOrderAPIView(RetrieveDestroyAPIView):
    queryset = CinemaMovieOrder.objects.filter(is_delete=False)
    serializer_class = CinemaMovieOrderSerializer
    # 添加认证，只能让用户自己删除订单
    authentication_classes = (CinemaUserAuthentication,)
    # 添加权限，只能删自己的
    permission_classes = (CinemaMovieOrderPermission,)

    # 删除订单（即修改is_delete属性，改写destroy方法）
    def destroy(self, request, *args, **kwargs):
        # 拿到对象
        instance = self.get_object()
        print(instance)

        # 差量更新，修改属性  partial=True：是否差量更新
        serializer = self.get_serializer(instance=instance, data={'is_delete': True}, partial=True)
        serializer.is_valid()
        serializer.save()

        return Response(serializer.data)


# 支付
# 支付接口，拿过来订单号，再给一个支付渠道，不和别的东西及联，所以继承自APIView,但是APIView不能做认证，所以可以继承GenericAPIView来做认证
class OrderPayAPIView(GenericAPIView):
    authentication_classes = (CinemaUserAuthentication,)
    permission_classes = (CinemaMovieOrderPermission)

    def post(self, request, *args, **kwargs):
        # 传订单编号和登录信息
        order_id = request.data.get('order_id')
        # 支付渠道
        pay_channel = request.data.get("pay_channel")

        order = CinemaMovieOrder.objects.get(pk=order_id)

        o_price = order.c_price

        order_id = 'cinema_movie' + order_id

        if pay_channel == 'alipay':

            subject = '电脑'

            alipay = AliPay(
                appid="APP_ID",
                app_notify_url=None,  # 默认回调url
                app_private_key_string=APP_PRIVATE_KEY,
                # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
                alipay_public_key_string=ALIPAY_PUBLIC_KEY,
                sign_type="RSA",  # RSA 或者 RSA2
                debug=True,  # 默认False
            )

            # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
            order_string = alipay.api_alipay_trade_page_pay(
                # 订单编号，项目中自动查询，添加
                out_trade_no=order_id,
                total_amount=o_price,
                subject=subject,

                # 现支付宝的通知有两类。
                # A服务器通知，对应的参数为notify_url，支付宝通知使用POST方式
                # B页面跳转通知，对应的参数为return_url，支付宝通知使用GET方式 （通知地址不需要像以前一样去账户内设置，而是由客户在支付的时候通过参数传递给我地址。

                # 付款后回调的url   页面重定向
                return_url="https://localhost:8000/cinema/oderpayed",
                # 服务器后台通知,这个页面是支付宝服务器端自动调用这个页面的链接地址,这个页面根据支付宝反馈过来的信息
                # 修改网站的定单状态,更新完成后需要返回一个success给支付宝.,不能含有任何其它的字符包括html语言.
                notify_url="https://localhost:8000/cinema/oderpayconfirm"  # 可选, 不填则使用默认notify url
            )

            pay_info = 'https://openapi.alipay.com/gateway.do?' + order_string



        elif pay_channel == 'wechat':
            pay_info = 'xxx'

        else:
            pay_info = 'yyy'

        data = {
            'msg': 'ok',
            'status': 200,
            'pay_url': pay_info,
        }

        return Response(data)


@api_view(['GET', 'POST'])
def order_pay_confirm(request):
    print(request.data)
    data = {
        'msg': 'ok',
        'status': 200,

    }
    return HttpResponse(data)


@api_view(['GET', 'POST'])
def order_payed(request):
    data = {
        'msg': 'pay success'
    }
    return Response(data)


# 获取影院、创建影院
class CinemasAPIView(ListCreateAPIView):
    queryset = Cinema.objects.all()
    serializer_class = CinemaSerializer
    # 创建post需要认证，查询get可以需要认证也可以不需要，比如影院登陆了可以只能看自己的
    authentication_classes = (CinemaUserAuthentication,)
    # 针对post，Get 不需要权限
    permission_classes = (CinemaPermission,)

    # Cinema表中有一个c_user字段，是及联影院用户表，因此重写post，让cinema及联上影院用户，得到用户id并save
    def perform_create(self, serializer):
        print(serializer)
        serializer.save(c_user_id=self.request.user.id)

    # 目的：调用get方法查看影院时，只能查看对应token创建的影院
    # 重写get方法中的list方法中的get_queryset
    def get_queryset(self):
        queryset = super(CinemasAPIView, self).get_queryset()
        # 判断user
        if isinstance(self.request.user, CinemaUser):
            queryset = queryset.filter(c_user=self.request.user)
        return queryset


class HallsAPIView(ListCreateAPIView):
    queryset = Hall.objects.all()
    serializer_class = HallSerializer
    authentication_classes = (CinemaUserAuthentication,)
    permission_classes = (CinemaPermission,)

    '''
    在permission中进行筛选了    
    
    # # 重写get，使得到指定影院的大厅
    # def get(self, request, *args, **kwargs):
    #     pass

    # def post(self, request, *args, **kwargs):
    #     h_cinema_id = self.request.data.get('h_cinema_id')
    #
    #     # 要确保大厅id是当前用户的，能进到这个步骤，代表有用户
    #     # request.user就是cinema_user
    #     # cinema_set：表Cinema通过外键c_user及联到CinemaUser上，则c_user是一个
    #     # 显性属性，而在CinemaUser上会生成一个隐形属性，隐形属性是:从表明小写_set
    #     cinema = request.user.cinema_set.filter(pk=h_cinema_id)
    #     if not cinema.exists():
    #         raise APIException(detail='请选择正确的影院')
    #
    #     request.h_cinema_id = h_cinema_id
    #     return self.create(request, *args, **kwargs)
    '''

    # 对结果集的筛选
    def get_queryset(self):
        queryset = super(HallsAPIView, self).get_queryset()
        queryset = queryset.filter(h_cinema_id=self.request.h_cinema_id)

        return queryset

    def perform_create(self, serializer):
        h_cinema_id = self.request.h_cinema_id
        serializer.save(h_cinema_id=h_cinema_id)


class PaiDangAPIView(ListCreateAPIView):
    queryset = PaiDang.objects.all()
    serializer_class = PaiDangSerializer

    authentication_classes = (CinemaUserAuthentication,)
    permission_classes = (CinemaPermission,)

    # 筛选：用时间、电影院、电影等筛选
    def get(self, request, *args, **kwargs):
        cinema_id = request.query_params.get('cinema_id')
        movie_id = request.query_params.get('movie_id')
        p_time = request.query_params.get('p_time')

        # 可以验证数据的合法性
        request.cinema_id = cinema_id
        request.movie_id = movie_id
        request.p_time = p_time

        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super(PaiDangAPIView, self).get_queryset()
        # 原时间字段p_time是DateTimeField，有日期和时间，现在传过来的只有日期
        # 切割，要让年月日都相等，时间是今天一天
        p_time = self.request.p_time

        year_month_day = p_time
        year, month, day = year_month_day.split('-')
        print('-----------------')
        print(p_time)
        print(year, month, day)

        queryset = queryset.filter(p_cinema_id=self.request.cinema_id).filter(p_movie_id=self.request.movie_id) \
            .filter(p_time__year=year)  # .filter(p_time__month=month).filter(p_time__day=day)
        return queryset

    def post(self, request, *args, **kwargs):
        # fields = ('p_time', 'p_price', 'p_hall_id', 'p_cinema_id')
        # 序列化中的'p_time', 'p_price'可以提供，
        # 'p_hall_id', 'p_cinema_id'是只读字段，需要自己验证
        p_hall_id = request.data.get('p_hall_id')
        p_cinema_id = request.data.get('p_cinema_id')

        # 要检测电影院是影院用户的，影厅是电影院的，拍档时间和别的不冲突
        cinemas = request.user.cinema_set.filter(pk=p_cinema_id)
        if not cinemas.exists():
            raise APIException(detail='请选择正确的影院')

        cinema = cinemas.first()

        halls = cinema.hall_set.filter(pk=p_hall_id)
        if not halls.exists():
            raise APIException(detail='请选择正确的大厅')

        # 电影是否购买
        # 在订单表中查询，查询当前用户，所购电影
        p_movie_id = request.data.get('p_movie_id')

        orders = CinemaMovieOrder.objects.filter(c_movie_id=p_movie_id).filter(c_user_id=request.user.id).filter(
            c_status=ORDER_PAY)

        if not orders.exists():
            raise APIException(detail='电影未购买')

        movie = Movie.objects.get(pk=p_movie_id)

        # p_time开始时间
        p_time = request.data.get('p_time')

        # p_time_end 结束时间=开始时间+电影时长+打扫时长
        times = p_time.split(' ')
        year, month, day = times[0].split('-')
        hour, minute, second = times[1].split(':')
        clean_time = 15
        # p_time_end = p_time + movie.m_duration + 15
        p_time_end = datetime.datetime(year=int(year), month=int(month), day=int(day), hour=int(hour),
                                       minute=int(minute), second=int(second)) + datetime.timedelta(
            minutes=movie.m_duration + clean_time)

        # e_start < n_start and e_end > n_end
        paidangs = PaiDang.objects.filter(Q(p_time__lte=p_time) & Q(p_time_end__gte=p_time_end))
        if paidangs.exists():
            raise APIException(detail='时间被包含')

        # e_end > n_start and e_end < n_end
        paidangs = PaiDang.objects.filter(Q(p_time_end__gte=p_time) & Q(p_time_end__lte=p_time_end))
        if paidangs.exists():
            raise APIException(detail='包含结束')

        # e_start > n_start and e_start < n_end
        paidangs = PaiDang.objects.filter(Q(p_time__gte=p_time) & Q(p_time_end__lte=p_time_end))
        if paidangs.exists():
            raise APIException(detail='包含开始')



        request.p_cinema_id = p_cinema_id
        request.p_hall_id = p_hall_id
        request.p_movie_id = p_movie_id
        request.p_time_end = '{}-{}-{} {}:{}:{}'.format(p_time_end.year, p_time_end.month, p_time_end.day,
                                                         p_time_end.hour, p_time_end.minute, p_time_end.second)

        return self.create(request, *args, **kwargs)

    # 修改创建过程
    def perform_create(self, serializer):
        serializer.save(p_hall_id=self.request.p_hall_id, p_cinema_id=self.request.p_cinema_id,
                        p_movie_id=self.request.p_movie_id, p_time_end=self.request.p_time_end)

    # 排档时间问题
    # 条件：
    # 1、不能排在当前时间之前（获取到时间后，和当前时间进行比较）
    # 2、排档提前：一天以上，提前一小时等等（在当前时间之上添加时间差）
    # 3、两个排档不能出现重叠时间（排档时间段内不能出现其他电影的开始或结束，时间之前和之后不能有同一个电影）
    # 4、排档的电影应该是已购买的