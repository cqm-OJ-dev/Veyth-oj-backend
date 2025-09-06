from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt

@api_view(['POST'])
@csrf_exempt  # 暂时禁用CSRF以测试
def test_conntect(request):
    message = request.data.get('message')
    if message == 'ok':
        return Response({'message': '连接成功'}, status=status.HTTP_200_OK)
    return Response({'message': '连接失败'}, status=status.HTTP_400_BAD_REQUEST)