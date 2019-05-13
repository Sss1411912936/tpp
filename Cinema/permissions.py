from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission

from Admin.models import AdminUser
from Cinema.models import CinemaUser


class AdminUserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            # users = request.user
            # for user in users:
            #     # print(user)
            #     # print('------------')
            #     # print(isinstance(user, AdminUser))
            #     return isinstance(user, AdminUser)

            user = request.user
            return isinstance(user, AdminUser)
        return True


class CinemaMovieOrderPermission(BasePermission):

    CNIEMA_USER_METHODS = ['POST', 'DELETE']
    def has_permission(self, request, view):
        # 根据方法区分
        # GET权限：user有值(管理员用户or影院用户)
        if request.method == 'GET':
            user = request.user
            return isinstance(user, AdminUser) or isinstance(user,CinemaUser)

        # 创建电影订单(是影院用户才能生成订单)
        elif request.method in self.CNIEMA_USER_METHODS:
            user = request.user
            return isinstance(user, CinemaUser)
        return False


class CinemaPermission(BasePermission):
    # 只有创建需要认证权限
    def has_permission(self, request, view):

        if type(view).__name__ == 'HallsAPIView':
            h_cinema_id = request.data.get('h_cinema_id') or request.query_params.get('h_cinema_id')

            # 要确保大厅id是当前用户的，能进到这个步骤，代表有用户
            # request.user就是cinema_user
            # cinema_set：表Cinema通过外键c_user及联到CinemaUser上，则c_user是一个
            # 显性属性，而在CinemaUser上会生成一个隐形属性，隐形属性是:从表明小写_set
            cinema = request.user.cinema_set.filter(pk=h_cinema_id)
            if not cinema.exists():
                raise APIException(detail='请选择正确的影院')

            request.h_cinema_id = h_cinema_id
            user = request.user
            return isinstance(user, CinemaUser)
        else:
            if request.method == 'POST':
                user = request.user
                return isinstance(user,CinemaUser)
        # 本来get方法是全都返回True可以请求的的，现在加了一个Get需要认证
        # elif request.method == 'GET' and type(view).__name__ == 'HallsAPIView':
        #     user = request.user
        #     return isinstance(user, CinemaUser)

        return True








