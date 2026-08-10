from django.http import JsonResponse
from .models import Problem

# Create your views here.

def get_problems(request):
    # 这里可以根据需要从数据库中获取题目列表
    problems = Problem.objects.all()
    data = []

    for problem in problems:
        submissions = problem.submissions or 0
        accepted = problem.accepted or 0
        acceptance = '0.0%'
        if submissions > 0:
            acceptance = f'{accepted / submissions * 100:.1f}%'

        data.append({
            'id': problem.id,
            'title': problem.title,
            'difficulty': problem.difficulty,
            'acceptance': acceptance,
            'submissions': submissions,
        })

    return JsonResponse({'problems': data}, status=200)