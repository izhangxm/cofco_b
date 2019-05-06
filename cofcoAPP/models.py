from django.db import models


# Create your models here.

class Journal(models.Model):
    id = models.AutoField(max_length=11, primary_key=True, auto_created=True)
    journal = models.CharField(max_length=300)
    ojournal = models.TextField()
    impact_factor = models.CharField(max_length=10)
    journal_zone = models.TextField()

    class Meta:
        db_table = 'spiderapp_journal'


class Content(models.Model):
    id = models.AutoField(max_length=11, primary_key=True, auto_created=True)
    project = models.TextField()
    sstr = models.TextField()
    source = models.TextField()
    status = models.IntegerField()  # 状态值，1:详情未爬取，2：详情已爬取，3：审核完毕
    doi = models.CharField(max_length=300, default='')
    ctime = models.IntegerField()
    pmid = models.TextField()
    title = models.TextField()
    author = models.TextField()
    journal = models.TextField()
    ojournal = models.TextField()
    impact_factor = models.TextField()
    journal_zone = models.TextField()
    issue = models.TextField()
    abstract = models.TextField()
    keyword = models.TextField()
    institue = models.TextField()
    irank = models.TextField()
    country = models.TextField()
    flink = models.TextField(default='')
    s_task_id = models.IntegerField(null=True)
    tag_id = models.IntegerField(null=True)
    tabstract = models.TextField(null=True)

    def __getattribute__(self, item):
        value = object.__getattribute__(self, item)
        return value


class SpiderKeyWord(models.Model):
    id = models.AutoField(max_length=11, primary_key=True, auto_created=True)
    keywords = models.TextField()
    value = models.TextField(null=True)
    status = models.IntegerField()
    ctime = models.IntegerField()

    class Meta:
        db_table = "hisi_admin_kw"


class AdminConfig(models.Model):
    id = models.AutoField(max_length=11, primary_key=True, auto_created=True)
    system = models.IntegerField()
    group = models.TextField(null=False)
    title = models.TextField(null=False)
    name = models.TextField(null=False)
    value = models.TextField(null=False)
    type = models.TextField(null=False)
    options = models.TextField(null=False)
    url = models.TextField(null=False)
    tips = models.TextField(null=False)
    sort = models.IntegerField()
    status = models.IntegerField()
    ctime = models.IntegerField()
    mtime = models.IntegerField()

    class Meta:
        db_table = 'hisi_admin_config'
