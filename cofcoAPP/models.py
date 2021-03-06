from django.db import models
from django.core import serializers
from django.db.models import QuerySet
import json

def get_json_model(object_s):
    results = {}
    if isinstance(object_s, QuerySet):
        query_set = json.loads(serializers.serialize('json', object_s))
        result = []
        for mode_r in query_set:
            result.append(mode_r['fields'])
    elif str(object_s.__class__.__bases__[0].__name__) == 'Model':
        results = json.loads(serializers.serialize('json',[object_s]))[0]['fields']
    return results

class Journal(models.Model):
    issn = models.TextField(primary_key=True)
    full_name = models.TextField()
    short_name = models.TextField()
    subject = models.TextField()
    journal_zone = models.IntegerField()
    impact_factor = models.FloatField()
    is_survey = models.TextField()
    is_top = models.TextField()
    total_cited = models.IntegerField()
    class Meta:
        db_table = 'cofco_admin_journal'


class Content(models.Model):
    art_id = models.TextField(max_length=64, primary_key=True)
    kw_id = models.IntegerField()
    project = models.TextField()
    status = models.IntegerField()  # 状态值，1:详情未爬取，2：详情已爬取，3：审核完毕
    doi = models.CharField(max_length=300, default='')
    ctime = models.IntegerField()
    title = models.TextField()
    author = models.TextField()
    issnl = models.TextField()
    issne = models.TextField()
    issnp = models.TextField()
    journal = models.TextField()
    impact_factor = models.FloatField()
    journal_zone = models.IntegerField()
    issue = models.TextField()
    abstract = models.TextField()
    keyword = models.TextField()
    institue = models.TextField()
    country = models.TextField()
    creater = models.TextField()
    tabstract = models.TextField(null=True)

    class Meta:
        db_table = "cofco_admin_content"


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
        db_table = "cofco_admin_kw"

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
        db_table = 'hisi_system_config'
