from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # 保留 AbstractUser 的所有默认字段：username / password / email / first_name / last_name / is_staff / is_active / date_joined / last_login / is_superuser
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    nickname = models.CharField('昵称', max_length=150, blank=True)
    avatar = models.URLField('头像URL', blank=True)
    bio = models.TextField('个人简介', blank=True)
    school = models.CharField('学校', max_length=100, blank=True)
    organization = models.CharField('机构', max_length=100, blank=True)
    country = models.CharField('国家/地区', max_length=50, blank=True)
    rating = models.IntegerField('OJ 评分', default=1500)
    solved_count = models.PositiveIntegerField('已解决题目数', default=0)
    submission_count = models.PositiveIntegerField('提交次数', default=0)
    accepted_count = models.PositiveIntegerField('通过次数', default=0)
    score = models.PositiveIntegerField('估值', default=0)
    last_submission_at = models.DateTimeField('最近提交时间', null=True, blank=True)
    is_banned = models.BooleanField('已封禁', default=False)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
