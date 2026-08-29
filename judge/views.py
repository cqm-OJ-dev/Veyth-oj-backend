from rest_framework import generics, serializers, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import ValidationError
from django.conf import settings
from django.shortcuts import get_object_or_404
from problems.models import Problem, TestCase
from .models import Submission, JudgeResult
from .sandbox import judge_all

def _allowed_langs():
    return getattr(settings, 'JUDGE_ALLOWED_LANGUAGES', ['python', 'cpp', 'java'])

class SubmissionCreateSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField(write_only=True)
    language = serializers.ChoiceField(choices=[(l, l) for l in _allowed_langs()])
    code = serializers.CharField(trim_whitespace=False)

class SubmissionSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    difficulty = serializers.CharField(source='problem.difficulty', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, default=None)

    class Meta:
        model = Submission
        fields = ['id', 'problem_id', 'problem_title', 'difficulty', 'language',
                  'status', 'total_cases', 'passed_cases', 'score',
                  'max_time_ms', 'max_memory_mb', 'username', 'created_at']
        read_only_fields = fields

class CaseResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = JudgeResult
        fields = ['case_index', 'status', 'time_ms', 'wall_time_ms',
                  'memory_kb', 'stdout', 'stderr', 'returncode']

class SubmissionDetailSerializer(SubmissionSerializer):
    case_results = CaseResultSerializer(many=True, read_only=True)
    code = serializers.CharField(read_only=True)
    error_message = serializers.CharField(read_only=True)

    class Meta(SubmissionSerializer.Meta):
        fields = SubmissionSerializer.Meta.fields + ['code', 'error_message', 'case_results']

class SubmissionCreateView(generics.CreateAPIView):
    serializer_class = SubmissionCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        problem = get_object_or_404(Problem, pk=data['problem_id'])
        tcs = list(problem.test_cases.all().order_by('order'))
        if not tcs:
            raise ValidationError('problem has no test cases')

        language = data['language']
        code = data['code']
        if len(code) > 100_000:
            raise ValidationError('code too large')

        tc_payload = [
            {
                'input': tc.input_data,
                'expected_output': tc.expected_output,
            }
            for tc in tcs
        ]
        time_limit_ms = max(tc.get_time_limit() for tc in tcs)
        memory_limit_mb = max(tc.get_memory_limit() for tc in tcs)
        submission = Submission.objects.create(
            user=request.user if request.user and request.user.is_authenticated else None,
            problem=problem,
            language=language,
            code=code,
            status='Judging',
            total_cases=len(tc_payload),
            passed_cases=0,
        )
        result = judge_all(language, code, tc_payload, time_limit_ms, memory_limit_mb)
        passed = result.get('passed', 0)
        total = result.get('total', len(tc_payload))
        overall_status = result.get('status', 'Internal Error')
        max_time = 0
        max_mem = 0
        score = 0
        errors = []
        for idx, r in enumerate(result.get('results', []), 1):
            t = r.get('time_ms') or 0
            wt = r.get('wall_time_ms') or 0
            if t > max_time:
                max_time = int(t)
            jr = JudgeResult.objects.create(
                submission=submission,
                case_index=r.get('case', idx),
                status=r.get('status', 'Internal Error'),
                time_ms=float(t),
                wall_time_ms=float(wt),
                stdout=r.get('stdout', ''),
                stderr=r.get('stderr', ''),
                returncode=int(r.get('returncode', 0) or 0),
            )
            if r.get('status') == 'Accepted':
                if idx - 1 < len(tcs):
                    score += tcs[idx - 1].score
            else:
                if r.get('stderr'):
                    errors.append(f"Case {jr.case_index}: {r['status']}")
                    if len(errors) < 3 and r.get('stderr'):
                        errors.append(r['stderr'][:200])

        submission.status = overall_status
        submission.passed_cases = passed
        submission.total_cases = total
        submission.score = score
        submission.max_time_ms = max_time
        submission.max_memory_mb = max_mem
        submission.error_message = '\n'.join(errors)[:2000]
        submission.save(update_fields=['status', 'passed_cases', 'total_cases', 'score', 'max_time_ms', 'max_memory_mb', 'error_message'])
        problem.submissions += 1
        if overall_status == 'Accepted':
            problem.accepted += 1
        problem.save(update_fields=['submissions', 'accepted'])

        return Response(SubmissionDetailSerializer(submission).data, status=status.HTTP_201_CREATED)

class SubmissionListView(generics.ListAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'max_time_ms']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Submission.objects.select_related('problem', 'user').all()
        pid = self.request.query_params.get('problem_id')
        if pid:
            qs = qs.filter(problem_id=pid)
        uid = self.request.query_params.get('user_id')
        if uid:
            qs = qs.filter(user_id=uid)
        lang = self.request.query_params.get('language')
        if lang:
            qs = qs.filter(language=lang)
        s = self.request.query_params.get('status')
        if s:
            qs = qs.filter(status=s)
        return qs

class SubmissionDetailView(generics.RetrieveAPIView):
    queryset = Submission.objects.select_related('problem', 'user').prefetch_related('case_results').all()
    serializer_class = SubmissionDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'

import json
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def evaluate_code(request):
    try:
        data = request.data or {}
        code = data.get('code', '')
        language = data.get('language', 'python')
        input_data = data.get('input', '') or ''

        if not code:
            return Response({'status': 'error', 'error': 'No code provided'},
                            status=status.HTTP_400_BAD_REQUEST)

        if language not in _allowed_langs():
            return Response({'status': 'error', 'error': f'unsupported language: {language}'},
                            status=status.HTTP_400_BAD_REQUEST)

        result = judge_all(
            language,
            code,
            test_cases=[{'input': input_data, 'expected_output': ''}],
            time_limit_ms=getattr(settings, 'JUDGE_DEFAULT_TIME_LIMIT_MS', 1000),
            memory_limit_mb=getattr(settings, 'JUDGE_DEFAULT_MEMORY_LIMIT_MB', 256),
        )
        first = result['results'][0] if result.get('results') else {}
        return Response({
            'status': 'success',
            'stdout': first.get('stdout', ''),
            'stderr': first.get('stderr', ''),
            'returncode': first.get('returncode', 0),
            'elapsed_ms': int(first.get('time_ms') or first.get('wall_time_ms') or 0),
            'error': None if first.get('status') in ('Accepted', 'Running') else first.get('status'),
            'case_status': first.get('status'),
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'status': 'error', 'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
