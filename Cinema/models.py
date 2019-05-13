from django.contrib.auth.hashers import make_password, check_password
from django.db import models

# Create your models here.

# 刚注册用户，还未认证（基有状态）
from Common.models import Movie

CINEMA_REGISTER = 0
# 激活了的用户
CINEMA_ACTIVE = 1
# 创建电影院权限auth_user
CINEMA_CAN_CREATE = 2
# 删除影院权限
CINEMA_CAN_DELETE = 4


class CinemaUser(models.Model):
    c_username = models.CharField(max_length=32, unique=True)
    c_password = models.CharField(max_length=256)
    is_delete = models.BooleanField(default=False)
    c_permission = models.IntegerField(default=CINEMA_REGISTER)

    # 封装检测权限的方法
    def check_permission(self, permission):
        return self.c_permission & permission == permission

    def set_password(self, password):
        self.c_password = make_password(password)
    def check_user_password(self, password):
        return check_password(password, self.c_password)


ORDER_NOT_PAY = 0  # 已下单，未付款
ORDER_PAY = 1  # 已下单，已付款


# 影院用户与电影，多对多
class CinemaMovieOrder(models.Model):
    c_user = models.ForeignKey(CinemaUser)  # 用户与订单是1--N关系
    c_movie = models.ForeignKey(Movie)  # 订单与电影是1—-N关系
    c_status = models.IntegerField(default=ORDER_NOT_PAY)  # 订单状态
    c_price = models.FloatField(default=0)      # 订单价钱
    is_delete = models.BooleanField(default=False)


# 电影院
class Cinema(models.Model):
    c_name = models.CharField(max_length=64)
    c_address = models.CharField(max_length=128)
    c_phone = models.CharField(max_length=32)
    # 审核电影院能否使用
    is_active = models.BooleanField(default=False)
    # 电影院属于的用户
    c_user = models.ForeignKey(CinemaUser)


# 大厅
class Hall(models.Model):
    h_cinema = models.ForeignKey(Cinema)
    h_name = models.CharField(max_length=32)
    # 座位表
    h_seats = models.CharField(max_length=256)


class PaiDang(models.Model):
    p_hall = models.ForeignKey(Hall)
    p_cinema = models.ForeignKey(Cinema)
    p_movie = models.ForeignKey(Movie)
    p_time = models.DateTimeField(default='2018-12-13 00:00:00')
    p_time_end = models.DateTimeField(default='2018-12-13 02:00:00')
    p_price = models.FloatField(default=35)

