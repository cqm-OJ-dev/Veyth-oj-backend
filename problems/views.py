from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Problem, Example, TestCase
from rest_framework import serializers

class ProblemListSerializer(serializers.ModelSerializer):
    acceptance = serializers.CharField(read_only=True)

    class Meta:
        model = Problem
        fields = ['id', 'title', 'difficulty', 'time_limit_ms', 'memory_limit_mb',
                  'acceptance', 'submissions']

    def get_acceptance(self, obj):
        if obj.submissions == 0:
            return '0.0%'
        return f'{obj.accepted / obj.submissions * 100:.1f}%'

class ExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Example
        fields = ['input_data', 'output_data', 'explanation']

class ProblemDetailSerializer(serializers.ModelSerializer):
    acceptance = serializers.CharField(read_only=True)
    examples = ExampleSerializer(many=True, read_only=True)

    class Meta:
        model = Problem
        fields = ['id', 'title', 'description', 'difficulty',
                  'time_limit_ms', 'memory_limit_mb',
                  'acceptance', 'submissions', 'accepted',
                  'examples', 'created_at', 'updated_at']

class ProblemListView(generics.ListAPIView):
    queryset = Problem.objects.all().order_by('id')
    serializer_class = ProblemListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['difficulty']
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'difficulty', 'submissions', 'created_at']
    pagination_class = None

class ProblemDetailView(generics.RetrieveAPIView):
    queryset = Problem.objects.all()
    serializer_class = ProblemDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'
