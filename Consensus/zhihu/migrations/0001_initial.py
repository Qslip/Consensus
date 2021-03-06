# Generated by Django 2.1.7 on 2019-05-15 12:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ZhihuAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arg', models.IntegerField(verbose_name='回答个数')),
            ],
        ),
        migrations.CreateModel(
            name='ZhihuInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('info', models.TextField(verbose_name='知乎回答')),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='zhihu.ZhihuAnswer', verbose_name='关联回答个数')),
            ],
        ),
        migrations.CreateModel(
            name='ZhihuQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('info_url', models.CharField(max_length=100, verbose_name='热榜网址')),
                ('question', models.CharField(max_length=30, verbose_name='知乎问题')),
            ],
        ),
        migrations.AddField(
            model_name='zhihuanswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='zhihu.ZhihuQuestion', verbose_name='关联知乎问题表'),
        ),
    ]
