from django.db import models


# Create your models here.
class Source(models.Model):
    describe = models.TextField(default='暂无描述内容')  # 源描述
    constant = models.TextField(null=True)  # 网页常量
    findpage = models.TextField(null=True)  # 搜索页面
    chapterpage = models.TextField(null=True)  # 章节页面
    contentpage = models.TextField(null=True)  # 正文页面
