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

        dict_Ranking = {}
        list_Ranking = []
        dict_movie = {}
        for movie in movies:
            print(movie.m_name,movie.price_total)
            dict_movie["电影名称"] = movie.m_name
            dict_movie["总票房"] = movie.price_totla
            dict_movie["电影类型"] = movie.m_mode
            dict_movie["上映日期"] = movie.m_open_day
            dict_movie["导演"] = movie.m_director
            dict_movie["主演"] = movie.m_leading_role
            dict_movie["电影时长"] = movie.m_duration
            list_Ranking.append(dict_movie)
        dict_Ranking["票行排行"] = list_Ranking

        data = {
            'msg':'OK',
            'status': 200,
            'Ranking':dict_Ranking,
        }

        return Response(data)