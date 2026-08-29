from django.db import models

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, default='Easy')
    time_limit_ms = models.PositiveIntegerField(default=1000)  # ms
    memory_limit_mb = models.PositiveIntegerField(default=256)  # MB
    submissions = models.PositiveIntegerField(default=0)
    accepted = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def acceptance_rate(self):
        if self.submissions == 0:
            return 0.0
        return round(self.accepted / self.submissions * 100, 1)

class Example(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='examples')
    input_data = models.TextField(blank=True)
    output_data = models.TextField(blank=True)
    explanation = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.problem.title} - Example {self.order}"

class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField(blank=True)
    expected_output = models.TextField(blank=True)
    time_limit_ms = models.PositiveIntegerField(default=0, help_text="0 表示沿用题目默认")
    memory_limit_mb = models.PositiveIntegerField(default=0, help_text="0 表示沿用题目默认")
    score = models.PositiveIntegerField(default=10)
    is_sample = models.BooleanField(default=False, help_text="是否为样例用例（可对用户展示输出）")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.problem.title} - TC#{self.order}"

    def get_time_limit(self):
        return self.time_limit_ms or self.problem.time_limit_ms

    def get_memory_limit(self):
        return self.memory_limit_mb or self.problem.memory_limit_mb
