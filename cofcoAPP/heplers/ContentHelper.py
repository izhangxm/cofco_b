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
from cofcoAPP.models import Content
from cofcoAPP import models

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

# 解析science_direct 文章详情的json字符串为一个content model对象
def format_scicent_details(detail_str):
    # TODO 解析science_direct的文章详情的json字符串，用于下一步的数据库存贮和序列化
    # TODO detail_str 为None时，构造一个失败结果对象
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
    content_model.issue = issue
    content_model.doi = doi
    content_model.title = title
    content_model.keyword = keyword

    return content_model


# 解析pubmed的xml为一个content model对象
def format_pubmed_xml(xml_str):
    # TODO 解析pubmed的xml为一个model对象，用于下一步的数据库存贮和序列化
    # TODO 当xml_str 为None时，构造一个失败结果对象
    #========= 预处理 ==================
    xml_str = html.unescape(xml_str)
    content_model = Content()
    root = ET.fromstring(xml_str)

    content = ['ELocationID', 'PMID', 'AbstractText', 'ArticleTitle','Title', 'ForeName', 'LastName', 'Year','Month','Day', 'Keyword', 'Country',
               'Author','time']
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
    a = list_['ForeName'].split(';')
    b = list_['LastName'].split(';')
    author = ''
    for p in range(len(a)):
        author += a[p] + b[p] + ','
    list_['Author'] = author[:-1]
    list_['time']=list_['Year']+list_['Month']+list_['Day']

    content_model.art_id = list_['PMID']
    content_model.author = list_['Author']
    content_model.country = list_['Country']
    content_model.issue = list_['time']
    content_model.abstract = list_['AbstractText']
    content_model.doi = list_['ELocationID']
    content_model.keyword = list_['Keyword']
    content_model.title = list_['ArticleTitle']
    content_model.journal = list_['Title']
    return content_model

def is_in_black_list(article_id):
    #TODO 判断是否在黑名单
    return False


def is_need_update(art_id):
    # 判断是否更新
    # 原则上 1一个月内刚刚爬取的文章不应该更新
    return True


# 保存或更新
def content_save(content_model):
    content_model.ctime = int(time.time())
    query_set = Content.objects.filter(art_id=content_model.art_id)
    if (len(query_set) > 0):
        kw_arg = models.get_json_model(content_model)
        Content.objects.filter(art_id=content_model.art_id).update(**kw_arg)
    else:
        content_model.save()

def is_deleted(article_id):
    #TODO 判断是否被删除
    return False


if __name__ == '__main__':
    pass
