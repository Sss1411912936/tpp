import datetime

from Cinema.models import PaiDang, ORDER_PAY, ORDER_NOT_PAY
from Viewer.models import ViewerOrder


def get_valid_seats(paidang_id, order_id=0):
    paidang = PaiDang.objects.get(pk=paidang_id)

    h_seats = paidang.p_hall.h_seats

    # 已经付款的座位
    orders_payed = ViewerOrder.objects.filter(v_status=ORDER_PAY).filter(v_paidang_id=paidang_id)

    # 未付款已锁定的座位,且订单未失效
    orders_locked = ViewerOrder.objects.filter(v_status=ORDER_NOT_PAY).filter(
        v_expire__gt=datetime.datetime.now()).filter(v_paidang_id=paidang_id)

    if order_id != 0:
        # exclude函数 (filter函数取反)
        orders_locked = orders_locked.exclude(pk=order_id)
        print('order_locked = ',orders_locked)
    # 剩下的可选择的座位
    h_seats_list = h_seats.split('#')
    print(orders_payed)
    orders_payed_seats = []
    for order_payed in orders_payed:
        orders_payed_seats += order_payed.v_seats.split('#')

    orders_locked_seats = []
    for order_locked in orders_locked:
        orders_locked_seats += order_locked.v_seats.split('#')

    print(h_seats_list)
    print('付款座位', orders_payed_seats)
    print('锁定座位', orders_locked_seats)

    valid_seats = list(set(h_seats_list) - set(orders_payed_seats) - set(orders_locked_seats))
    print('可用座位', valid_seats)

    return valid_seats
