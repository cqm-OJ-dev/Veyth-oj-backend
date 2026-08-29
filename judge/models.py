from django.db import models
from django.conf import settings
from problems.models import Problem

class Submission(models.Model):
    LANG_CHOICES = [(l, l) for l in settings.JUDGE_ALLOWED_LANGUAGES]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Judging', 'Judging'),
        ('Accepted', 'Accepted'),
        ('Wrong Answer', 'Wrong Answer'),
        ('Time Limit Exceeded', 'Time Limit Exceeded'),
        ('Memory Limit Exceeded', 'Memory Limit Exceeded'),
        ('Runtime Error', 'Runtime Error'),
        ('Compile Error', 'Compile Error'),
        ('Output Limit Exceeded', 'Output Limit Exceeded'),
        ('Internal Error', 'Internal Error'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions', null=True, blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='submission_set')
    language = models.CharField(max_length=20, choices=LANG_CHOICES)
    code = models.TextField()
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='Pending')
    total_cases = models.PositiveIntegerField(default=0)
    passed_cases = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
    max_time_ms = models.PositiveIntegerField(default=0)
    max_memory_mb = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission #{self.id} - {self.problem.title} - {self.status}"

class JudgeResult(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='case_results')
    case_index = models.PositiveSmallIntegerField()  # 第几个用例
    status = models.CharField(max_length=40, choices=Submission.STATUS_CHOICES)
    time_ms = models.FloatField(default=0)
    wall_time_ms = models.FloatField(default=0)
    memory_kb = models.PositiveIntegerField(default=0)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    returncode = models.IntegerField(default=0)

    class Meta:
        ordering = ['case_index']
