from django.db import models

# Create your models here.


class SpecialSubject(models.Model):
    """
    微博专题信息数据表
    """
    title = models.CharField(max_length=200, unique=True, verbose_name='专题名称')
    desc = models.CharField(max_length=300, null=True, verbose_name='专题描述')
    midtext = models.CharField(max_length=100, null=True, verbose_name='专题阅读、讨论量')
    downtext = models.CharField(max_length=100, null=True, verbose_name='专题主持人')
    background_url = models.CharField(max_length=200, null=True, verbose_name='专题背景图片链接')
    portrait = models.CharField(max_length=200, null=True, verbose_name='专题头像链接')

    def __str__(self):
        return self.title


class MicroBlog(models.Model):
    """
    微博信息数据表
    """
    detail_url = models.CharField(max_length=200, verbose_name='微博链接')
    micro_blog_id = models.CharField(max_length=100, unique=True, verbose_name='微博ID')
    content = models.TextField(verbose_name='微博内容')
    subject = models.CharField(max_length=200, null=True, verbose_name='微博主题')
    video_url = models.CharField(max_length=200, null=True, verbose_name='微博视频链接')
    video_count = models.PositiveIntegerField(null=True, verbose_name='微博视频观看次数')
    created_at = models.CharField(max_length=50, verbose_name='创建时间')
    write_at = models.DateTimeField(auto_now_add=True, verbose_name='写入数据库时间')
    comment_count = models.PositiveIntegerField(verbose_name='微博评论数量')
    like_count = models.PositiveIntegerField(default=0, verbose_name='微博点赞数量')
    transmit_count = models.PositiveIntegerField(default=0, verbose_name='微博转发数量')
    author = models.CharField(max_length=150, verbose_name='微博作者名称')
    author_description = models.CharField(max_length=300, verbose_name='微博作者描述')
    author_profile = models.CharField(max_length=200, verbose_name='微博作者头像')
    author_url = models.CharField(max_length=200, verbose_name='微博作者链接')
    source = models.CharField(max_length=50, verbose_name='微博来源：如iPhone')

    special_subject = models.ForeignKey(SpecialSubject, null=True,
                                        on_delete=models.DO_NOTHING, verbose_name='关联专题')

    def __str__(self):
        return self.content

    class Meta:
        ordering = ['write_at']


class MbImg(models.Model):
    """
    微博图片的URL，一条微博可以有多个图片
    """
    img_url = models.CharField(max_length=200, verbose_name='微博图片链接地址')
    micro_blog = models.ForeignKey(MicroBlog, on_delete=models.DO_NOTHING, verbose_name='关联微博信息')

    def __str__(self):
        return self.micro_blog.content


class Comment(models.Model):
    """
    微博评论内容数据表，一条微博可以有多条评论
    """
    comment_content = models.CharField(max_length=500, verbose_name='微博评论内容')
    author_name = models.CharField(max_length=150, verbose_name='评论的用户名字')
    author_description = models.CharField(max_length=200, verbose_name='评论的用户个人描述')
    author_profile = models.CharField(max_length=200, verbose_name='评论的用户头像链接')
    author_url = models.CharField(max_length=200, verbose_name='评论的用户个人中心链接')
    created_at = models.CharField(max_length=50, verbose_name='微博评论时间')
    write_at = models.DateTimeField(auto_now_add=True, verbose_name='评论写入数据库时间')

    micro_blog = models.ForeignKey(MicroBlog, on_delete=models.DO_NOTHING, verbose_name='关联微博信息')

    def __str__(self):
        return self.micro_blog.content
