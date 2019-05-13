from django.shortcuts import render

# Create your views here.
from rest_framework.generics import ListCreateAPIView

from Admin.authentication import AdminUserAuthentication
from Admin.permissions import SuperAdminUserPermission
from Common.models import Movie
from Common.serializers import MovieSerializer


class MoviesAPIView(ListCreateAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    # 超级管理员可以创建，查看所有人都可查看
    authentication_classes = (AdminUserAuthentication,)
    permission_classes = (SuperAdminUserPermission,)
