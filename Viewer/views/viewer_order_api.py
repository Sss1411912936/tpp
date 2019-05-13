import datetime

from rest_framework.exceptions import APIException
from rest_framework.generics import ListCreateAPIView

from Cinema.models import PaiDang
from Viewer.controller import get_valid_seats
from Viewer.models import ViewerOrder
from Viewer.permission import ViewerUserPermission
from Viewer.serializers import ViewerOrderSerializer
from Viewer.authentication import ViewerUserAuthentication


class ViewerOrdersAPIView(ListCreateAPIView):
    queryset = ViewerOrder.objects.all()
    serializer_class = ViewerOrderSerializer
    authentication_classes = (ViewerUserAuthentication,)
    permission_classes = (ViewerUserPermission, )

    # post创建中有一部分是只读的，所以要自己实现
    # 校验只读参数v_user，v_paidang
    def post(self, request, *args, **kwargs):
        v_user_id = request.user.id
        v_paidang_id = request.data.get('v_paidang_id')
        v_seats = request.data.get('v_seats')

        # 判定提供的座位是否可用
        valid_seats = get_valid_seats(v_paidang_id)

        if set(valid_seats) & set(v_seats.split('#')) != set(v_seats.split('#')):
            raise APIException(detail='锁坐失败')
        # 买的座位数量
        seat_count = len(v_seats.split('#'))

        # 找到排档，以此得到一张票的钱
        paidang = PaiDang.objects.get(pk=v_paidang_id)
        v_single_price = paidang.p_price

        # 总价钱
        v_price = seat_count * v_single_price

        request.v_user_id = v_user_id
        request.v_price = v_price
        request.v_paidang_id = v_paidang_id
        request.v_seats = v_seats

        return self.create(request, *args, **kwargs)



    def perform_create(self, serializer):
        expire_time = datetime.datetime.now() + datetime.timedelta(minutes=15)
        serializer.save(v_expire=expire_time,v_seats=self.request.v_seats, v_price=self.request.v_price,v_user_id=self.request.v_user_id,v_paidang_id=self.request.v_paidang_id )

        # 乐观锁 判定剩的坐和锁的坐之间的关系是不是操作的差。
        # 看除了自己的订单外，看看有没有别的人把它买走了
        # 即检查除自己的订单外，看还有没有其他订单包含我们的座位
        print('self.request.v_seats = ', self.request.v_seats)
        print('serializer.instance.id = ',serializer.instance.id)
        valid_seats = get_valid_seats(self.request.v_paidang_id,serializer.instance.id)
        print('除自己外，未付款，没锁定的座位', valid_seats)

        # 如果 除自己外，未付款，没锁定的座位 里面包含自己全部选定的座位，则证明没有人操作数据
        # 如果 不包含自己选定的座位，则证明有人也选定了座位，则比较时间，如果自己时间靠前，就继续购买，自己时间靠后，则把自己删除
        if set(valid_seats) & set(self.request.v_seats.split('#')) != self.request.v_seats.split('#'):
            # 查询座位几次操作的时间
            # 自己操作的数据：sereializer.instance
            # 别人操作的数据：根据座位找订单，根据订单找时间

            # 以自己的时间（之前）和座位去查找，找到，删除自己
            # 座位筛选
            viewerorders = ViewerOrder.objects.filter(v_paidang_id=self.request.v_paidang_id).filter(v_expire__lte=serializer.instance.v_expire)

            orders_seats = []
            for viewer_order in viewerorders:
                orders_seats += viewer_order.v_seats.split('#')

            if set(orders_seats) & set(self.request.v_seats.split('#')):
                # 有交集，删除自己
                serializer.instance.delete()
                raise APIException(detail='锁单失败，有人比你手快')










