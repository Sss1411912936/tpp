from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from Common.models import Movie


class TicketTopAPIView(APIView):
    def get(self,request,*args,**kwargs):
        # Movie.objects.aggregate()  aggregate()求聚合的值
        # Movie.objects.annotate()   annotate()在原来的movie表中加上一个字段，坐及联
        # 调用栈
        movies = Movie.objects.annotate(price_total=Sum('paidang__viewerorder__v_price')).order_by('-price_total')

        print(movies)
        print(movies.query)

        for movie in movies:
            print(movie.m_name,movie.price_total)



        data = {
            'msg':'OK',
            'status': 200,
        }

        return Response(data)