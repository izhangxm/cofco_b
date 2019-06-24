#! /usr/bin/python
# -*- coding: utf-8 -*-
# @author izhangxm
# Copyright 2017 izhangxm@gmail.com. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
# from cofcoAPP.heplers import  __initDjangoEnvironment
import json
import html
import time
import re
from cofcoAPP.models import Content, Journal

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

# 解析science_direct 文章详情的json字符串为一个content model对象
def format_scicent_details(detail_str):
    content = []
    def analyze_json(jsons):
        if isinstance(jsons, dict):
            for key in jsons.keys():
                key_value = jsons.get(key)
                if isinstance(key_value, dict):
                    analyze_json(key_value)
                elif isinstance(key_value, list):
                    for json_array in key_value:
                        analyze_json(json_array)
                else:
                    if key == '_':
                        content.append(key_value)
        elif isinstance(jsons, list):
            for json_array in jsons:
                analyze_json(json_array)
        return content

    #========= 预处理 ==================
    content_model = Content()

    js = json.loads(detail_str)
    try:
        abstract = ''
        abs = js['abstracts']['content']
        abs = analyze_json(abs)
        for i in abs:
            if i != 'Abstract':
                abstract = abstract + ' ' + str(i)
        abstract = abstract[1:]
    except:
        abstract = ''

    try:
        author = ''
        aut = js['authors']['content'][0]['$$']
        tem1 = 0
        tem2 = 0
        name = []
        inco = ''
        for i in aut:
            if i['#name'] == 'author' and tem1 == 0:
                name = i['$$']
                tem1 = tem1 + 1
            if i['#name'] == 'affiliation':
                ic = i['$$']
                for j in ic:
                    if j['#name'] == 'textfn' and tem2 == 0:
                        inco = j['_']
                        tem2 = tem2 + 1

        firstname = ''
        lastname = ''
        for i in name:
            if i['#name'] == 'given-name':
                firstname = i['_']
            if i['#name'] == 'surname':
                lastname = i['_']
        orgn = inco.split(',')
        author = firstname + ' ' + lastname
        country = orgn[-1]
        institue = inco
    except:
        author = ''
        country = ''
        institue = ''
    try:
        date = js['article']['dates']['Publication date']
    except:
        date = ''

    try:
        doi = js['article']['doi']
    except:
        doi = ''
    try:
        title = js['article']['title']['content']
        for i in title:
            if i['#name'] == 'title':
                title = i['_']
                break
    except:
        title = ''

    try:
        keyword = ''
        key = js['combinedContentItems']['content']
        for i in key:
            if i['#name'] == 'keywords':
                for j in i['$$']:
                    if j['#name'] == 'keywords':
                        for p in j['$$']:
                            if p['#name'] == 'keyword':
                                for y in p['$$']:
                                    keyword = keyword + ';' + y['_']
        keyword = keyword[1:]
    except:
        keyword = ''

    issue = date
    content_model.abstract = abstract
    content_model.author = author
    content_model.country = country[1:]
    content_model.institue = institue
    try:
        content_model.issue = time.strftime('%Y-%m-%d',time.strptime(issue,'%d %B %Y'))
    except Exception:
        content_model.issue = issue

    # 处理issn
    r = re.search(r'issn-primary-formatted":"([\s\S]*?)"', detail_str)
    if r:
        content_model.issnl = r.group(1)

    content_model.doi = doi
    content_model.title = title
    content_model.keyword = keyword

    return content_model


# 解析pubmed的xml为一个content model对象
def format_pubmed_xml(xml_str):
    #========= 预处理 ==================
    xml_str = html.unescape(xml_str)
    content_model = Content()
    root = ET.fromstring(xml_str)

    content = ['ELocationID', 'PMID', 'AbstractText', 'ArticleTitle','Title', 'Initials', 'LastName', 'Year','Month','Day', 'Keyword', 'Country',
               'Author','time','ISSNLinking']
    value = []
    for list_ in content:
        keywords_ele = root.findall('.//' + list_)
        keywords = ''
        i = 0
        for kw_ele in keywords_ele:
            if kw_ele!='Author' and kw_ele!='time' and str(kw_ele.text)!='None':
                keywords += str(kw_ele.text) + ';'
                if list_ == 'Year' or list_ == 'Month' or list_ == 'Day':
                    break
        value.append(keywords[:-1])

    list_ = dict(map(lambda x, y: [x, y], content, value))
    a = list_['Initials'].split(';')
    b = list_['LastName'].split(';')
    author = ''
    for p in range(len(a)):
        author += b[p] + ' ' + a[p] + ';'
    list_['Author'] = author[:-1]
    list_['time']=list_['Year']+list_['Month']+list_['Day']

    content_model.art_id = list_['PMID']
    content_model.author = list_['Author']
    content_model.country = list_['Country']
    try:
        content_model.issue = time.strftime('%Y-%m-%d',time.strptime(list_['time'],'%Y%m%d'))
    except Exception:
        content_model.issue = list_['time']
    content_model.abstract = list_['AbstractText']
    content_model.doi = list_['ELocationID']
    if content_model.doi == '':
        r = re.search(r'<ArticleId IdType="doi">([\s\S]*?)</ArticleId>',xml_str)
        if r:
            content_model.doi = r.group(1)
    content_model.issnl = list_['ISSNLinking']

    r = re.search(r'<ArticleId IdType="doi">([\s\S]*?)</ArticleId>', xml_str)
    content_model.doi = r.group(1) if r else ''

    r = re.search(r'ISSN IssnType="Electronic">([\s\S]*?)</ISSN>',xml_str)
    content_model.issne = r.group(1) if r else ''

    r = re.search(r'ISSN IssnType="Print">([\s\S]*?)</ISSN>', xml_str)
    content_model.issnp = r.group(1) if r else ''

    r = re.findall(r'<Affiliation>([\s\S]*?)</Affiliation>', xml_str)
    institue = ''
    for ins in r:
        institue += ins+';'
    content_model.institue = institue
    content_model.keyword = list_['Keyword']
    content_model.title = list_['ArticleTitle']
    content_model.journal = list_['Title']

    # 处理期刊信息
    content_model.impact_factor = None
    content_model.journal_zone = None
    # 寻找最可能的结果
    result = None
    try:
        result = Journal.objects.filter(issn=content_model.issnl)
        if result:
            raise Exception('')
        result = Journal.objects.filter(issn=content_model.issne)
        if result:
            raise Exception('')

        result = Journal.objects.filter(issn=content_model.issnp)
        if result:
            raise Exception('')

        result = Journal.objects.filter(full_name__icontains=content_model.journal)  # 通过期刊名称模糊查询
        if result:
            raise Exception('')

    except Exception:
        if result:
            journal = result[0]
            content_model.impact_factor = journal.impact_factor
            content_model.journal_zone = journal.journal_zone
    return content_model

def is_in_black_list(art_id):
    ori_content = Content.objects.filter(art_id=art_id)
    if (ori_content and ori_content[0].art_id == '-2'):
        return True
    return False

# 保存或更新
def content_save(content_model):
    content_model.ctime = int(time.time())
    content_model.impact_factor = None
    content_model.journal_zone = None
    # 寻找最可能的结果
    result = None
    try:
        result = Journal.objects.filter(issn=content_model.issnl)
        if result:
            raise Exception('')
        result = Journal.objects.filter(issn=content_model.issne)
        if result:
            raise Exception('')

        result = Journal.objects.filter(issn=content_model.issnp)
        if result:
            raise Exception('')

        result = Journal.objects.filter(full_name__icontains=content_model.journal)  # 通过期刊名称模糊查询
        if result:
            raise Exception('')

    except Exception:
        if result:
            journal = result[0]
            content_model.impact_factor = journal.impact_factor
            content_model.journal_zone = journal.journal_zone
    finally:
        ori_content = Content.objects.filter(art_id=content_model.art_id)
        if(ori_content):
            content_model.__delattr__('status')
        content_model.save()

if __name__ == '__main__':
    pass
