import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from Cinema.models import PaiDang
from Viewer.authentication import ViewerUserAuthentication
from Viewer.controller import get_valid_seats
from Viewer.models import ViewerOrder, ORDERED_PAYED, ORDERED_NOT_PAY
from Viewer.permission import ViewerUserPermission


class SeatsAPIView(APIView):

    authentication_classes = (ViewerUserAuthentication,)
    permission_classes = (ViewerUserPermission,)
    def get(self,request,*arg,**kwargs):
        paidang_id = request.query_params.get('paidang_id')

        vaild_seats = '#'.join(get_valid_seats(paidang_id))

        data = {
            'msg': 'ok',
            'valid_seats': vaild_seats,


        }

        return Response(data)







