from django.db import models
from django.core import serializers
from django.db.models import QuerySet
import json

def get_json_model(object_s):
    result = {}
    if isinstance(object_s,QuerySet):
        query_set = json.loads(serializers.serialize('json', object_s))
        result = []
        for mode_r in query_set:
            result.append(mode_r['fields'])
    elif str(object_s.__class__.__bases__[0].__name__) == 'Model':
        result = json.loads(serializers.serialize('json',[object_s]))[0]['fields']
    return result

class Journal(models.Model):
    id = models.AutoField(max_length=11, primary_key=True, auto_created=True)
    journal = models.CharField(max_length=300)
    ojournal = models.TextField()
    impact_factor = models.CharField(max_length=10)
    journal_zone = models.TextField()

    class Meta:
        db_table = 'spiderapp_journal'


class Content(models.Model):
    art_id = models.TextField(max_length=11, primary_key=True)
    kw_id = models.IntegerField()
    project = models.TextField()
    status = models.IntegerField()  # 状态值，1:详情未爬取，2：详情已爬取，3：审核完毕
    doi = models.CharField(max_length=300, default='')
    ctime = models.IntegerField()
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
    tabstract = models.TextField(null=True)

    class Meta:
        db_table = "spiderapp_content"



class SpiderKeyWord(models.Model):
    id = models.AutoField(max_length=11, primary_key=True, auto_created=True)
    name = models.TextField(null=True)
    type = models.TextField(null=True)
    value = models.TextField(null=True)
    uid = models.TextField(null=True)
    sstatus = models.IntegerField(null=True)
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
