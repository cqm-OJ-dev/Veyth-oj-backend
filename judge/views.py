from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .sandbox import run_in_sandbox

@csrf_exempt
@api_view(['POST'])
def evaluate_code(request):
    try:
        # 1. 从POST请求中获取代码和语言
        code = request.POST.get('code', '')
        language = request.POST.get('language', 'python')  # 默认为Python
        if not code:
            return Response({'status': 'error', 'message': 'No code provided'},status=status.HTTP_400_BAD_REQUEST)

        # 3. 设置沙箱执行环境
        result = run_in_sandbox(code, language)
        
        return Response({'status': 'success', 'result': result}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
