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
from cofcoAPP.models import Content
import jsonpath
import json
import html
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import MySQLdb
content=[]
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
                # print(str(key) + " = " + str(key_value))
                if key=='_':
                    content.append(key_value)
    elif isinstance(jsons, list):
        for json_array in jsons:
            analyze_json(json_array)
    return content

def dejson(jsoninfo,content_model):
    js = json.loads(jsoninfo)
    try:
        abstract = ''
        abs = js['abstracts']['content']
        abs = analyze_json(abs)
        for i in abs:
            if i != 'Abstract':
                abstract = abstract + ' ' + str(i)
        abstract = abstract[1:]
        content = []
    except:
        abstract = 'wu'
        content = []
    try:
        author = ''
        aut = js['authors']['content'][0]['$$']
        tem1 = 0
        tem2 = 0
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

    content_model.abstract=abstract
    content_model.author=author
    content_model.country=country[1:]
    content_model.institue=institue
    content_model.issue=issue
    content_model.doi=doi
    content_model.title=title
    content_model.keyword=keyword
    return content_model
def list_dic(list1,list2):
    '''
    two lists merge a dict,a list as key,other list as value
    :param list1:key
    :param list2:value
    :return:dict
    '''
    dic = dict(map(lambda x,y:[x,y], list1,list2))
    return dic
def add(list,content_model):
    content_model.author=list['Author']
    content_model.country=list['Country']
    content_model.issue=list['Year']
    content_model.abstract=list['AbstractText']
    content_model.doi=list['ELocationID']
    content_model.keyword=list['Keyword']
    content_model.title=list['ArticleTitle']
    content_model.pmid=list['PMID']
    content_model.journal = list['Title']

    return content_model

# 解析science_direct 文章详情的json字符串为一个content model对象
def format_scicent_details(detail_str):
    # TODO 解析science_direct的文章详情的json字符串，用于下一步的数据库存贮和序列化
    # TODO detail_str 为None时，构造一个失败结果对象
    #========= 预处理 ==================
    content_model = Content()
    jsons1 = detail_str
    content_model=dejson(jsons1,content_model)
    return content_model


# 解析pubmed的xml为一个content model对象
def format_pubmed_xml(xml_str):
    # TODO 解析pubmed的xml为一个model对象，用于下一步的数据库存贮和序列化
    # TODO 当xml_str 为None时，构造一个失败结果对象
    #========= 预处理 ==================
    xml_str = html.unescape(xml_str)
    content_model = Content()
    root = ET.fromstring(xml_str)

    #========= keywords ===============
    content = ['ELocationID', 'PMID', 'AbstractText', 'ArticleTitle','Title', 'ForeName', 'LastName', 'Year', 'Keyword', 'Country',
               'Author']
    value = []
    for list in content:
        keywords_ele = root.findall('.//' + list)
        keywords = ''
        i = 0
        for kw_ele in keywords_ele:
            # print(type(kw_ele))
            if kw_ele!='Author' and str(kw_ele.text)!='None':
                keywords += str(kw_ele.text) + ';'
                if list == 'Year':
                    break
        # print(keywords)
        value.append(keywords[:-1])
    list = list_dic(content, value)
    a = list['ForeName'].split(';')
    b = list['LastName'].split(';')
    author = ''
    for p in range(len(a)):
        author += a[p] + b[p] + ','
    list['Author'] = author[:-1]
    content_model=add(list,content_model)
    return content_model

def is_in_black_list(article_id):
    #TODO 判断是否在黑名单
    return False

def is_deleted(article_id):
    #TODO 判断是否被删除
    return False

def ke_test():
    from cofcoAPP.models import SpiderKeyWord
    a = SpiderKeyWord.objects.filter(id=74).values()

if __name__ == '__main__':
    # print(format_pubmed_xml('aa').author)
    model=format_scicent_details('aa')
    model.save()
    # db = MySQLdb.connect("localhost", "root", "root", "cofco", charset='utf8')
    # cursor = db.cursor()
    # sql = """INSERT INTO spiderapp_content(title)
    #          VALUES (%s)"""%(model.title)
    # print(model.title)
    # try:
    #     cursor.execute(sql)
    #     db.commit()
    # except:
    #     db.rollback()
    # db.close()
    pass
