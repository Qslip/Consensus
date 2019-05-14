from django.db import models

# Create your models here.

class ZhihuQuestion(models.Model):
    info_url = models.CharField(max_length=100, verbose_name='热榜网址')
    question = models.CharField(max_length=30, verbose_name='知乎问题')
    

class ZhihuAnswer(models.Model):
    question = models.ForeignKey(ZhihuQuestion, on_delete=models.CASCADE, verbose_name='关联知乎问题表')
    arg = models.IntegerField(verbose_name='回答个数')

class ZhihuInfo(models.Model):
    answer = models.ForeignKey(ZhihuAnswer, on_delete=models.CASCADE, verbose_name='关联回答个数')
    info = models.TextField(verbose_name='知乎回答')


