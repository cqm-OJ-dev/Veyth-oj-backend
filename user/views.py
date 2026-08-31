import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

User = get_user_model()


def _user_payload(user):
    """构造返回给前端的用户信息"""
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'nickname': user.nickname,
        'avatar': user.avatar,
        'is_staff': user.is_staff,
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    try:
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if User.objects.filter(username=username).exists():
            return Response({'error': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({'message': '注册成功'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': _user_payload(user),
        }, status=status.HTTP_200_OK)
    else:
        return Response({'error': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def github_callback(request):
    """GitHub OAuth 回调：用 code 换取 access_token，再获取用户信息，创建/登录用户，返回 JWT"""
    code = request.data.get('code')
    if not code:
        return Response({'error': '缺少 code 参数'}, status=status.HTTP_400_BAD_REQUEST)

    # 1. 用 code 向 GitHub 换取 access_token
    try:
        token_resp = requests.post(
            'https://github.com/login/oauth/access_token',
            json={
                'client_id': settings.GITHUB_CLIENT_ID,
                'client_secret': settings.GITHUB_CLIENT_SECRET,
                'code': code,
            },
            headers={'Accept': 'application/json'},
            timeout=15,
        )
        token_data = token_resp.json()
    except Exception:
        return Response({'error': 'GitHub token 交换请求失败'}, status=status.HTTP_502_BAD_GATEWAY)

    gh_token = token_data.get('access_token')
    if not gh_token:
        err_desc = token_data.get('error_description') or token_data.get('error') or 'token 交换失败'
        return Response({'error': err_desc}, status=status.HTTP_400_BAD_REQUEST)

    # 2. 获取 GitHub 用户信息
    try:
        user_resp = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'Bearer {gh_token}', 'Accept': 'application/json'},
            timeout=15,
        )
        gh_user = user_resp.json()
    except Exception:
        return Response({'error': 'GitHub 用户信息获取失败'}, status=status.HTTP_502_BAD_GATEWAY)

    gh_user_id = gh_user.get('id')
    gh_login = gh_user.get('login')
    gh_email = gh_user.get('email')
    gh_avatar = gh_user.get('avatar_url')
    gh_name = gh_user.get('name') or gh_login

    if not gh_user_id or not gh_login:
        return Response({'error': 'GitHub 用户信息不完整'}, status=status.HTTP_400_BAD_REQUEST)

    # 3. 如果 user 接口没返回邮箱，调 /user/emails 获取主邮箱
    if not gh_email:
        try:
            emails_resp = requests.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'Bearer {gh_token}', 'Accept': 'application/json'},
                timeout=15,
            )
            emails = emails_resp.json()
            for e in (emails if isinstance(emails, list) else []):
                if e.get('primary'):
                    gh_email = e.get('email')
                    break
        except Exception:
            pass  # 邮箱非必需，继续

    # 4. 查找或创建 Django 用户（GitHub ID 唯一标识）
    username = f'github_{gh_user_id}'
    user = User.objects.filter(username=username).first()
    if user is None:
        user = User.objects.create_user(
            username=username,
            email=gh_email or '',
            password=User.objects.make_random_password(length=32),
        )

    # 更新 GitHub 同步的资料
    changed = False
    if gh_avatar and user.avatar != gh_avatar:
        user.avatar = gh_avatar
        changed = True
    if gh_name and user.nickname != gh_name:
        user.nickname = gh_name
        changed = True
    if gh_email and user.email != gh_email:
        user.email = gh_email
        changed = True
    if changed:
        user.save()

    # 5. 生成 JWT 返回
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': _user_payload(user),
    }, status=status.HTTP_200_OK)
