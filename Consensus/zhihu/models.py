from django.db import models

# Create your models here.

class ZhihuUrl(models.Model):
    info_url = models.CharField(max_length=100, verbose_name='热榜网址')
    question = models.CharField(max_length=30, verbose_name='新闻题目')
    

class ZhiInfo(models.Model):
    question = models.ForeignKey(ZhihuUrl, on_delete=models.CASCADE)
    answer = models.TextField()


