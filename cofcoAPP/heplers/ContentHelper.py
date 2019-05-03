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
from cofcoAPP.heplers import  __initDjangoEnvironment
from cofcoAPP.models import Content
import jsonpath
import json
import html
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

def dejson(jsoninfo,content_model):
    js = json.loads(jsoninfo)
    abstract = js['abstracts']
    author = js['authors']['content']
    date = js['article']['dates']
    doi = js['article']['doi']
    title = js['article']['title']
    keyword = js['combinedContentItems']
    abstract = jsonpath.jsonpath(abstract, '$.._')
    author = jsonpath.jsonpath(author, '$.._')
    title = jsonpath.jsonpath(title, '$.._')
    keyword = jsonpath.jsonpath(keyword, '$.._')
    ab = ''
    key = ''
    for i in abstract[1:]:
        if i == 'Graphical abstract':
            break
        if i[0] == '”' or i[0] == '“':
            ab += i
        else:
            ab += '\n' + i
    ab=ab[1:]
    aut = []
    ins = ''
    authors1 = ''
    aut1 = []
    for i in author:
        if len(i) < 2 or '@' in i:
            continue
        else:
            aut.append(i)

    for i in range(len(aut)):
        if len(aut[i]) > 15:
            ins = aut[i]
            break
        else:
            aut1.append(aut[i])
    for i in range(1, len(aut1) + 1):
        if i % 2 == 0:
            authors1 += aut1[i - 1] + ';'
        else:
            authors1 += aut1[i - 1] + ' '
    contory = aut[-2]
    date = date['Accepted']
    title = title[0]
    for i in keyword[1:]:
        key += ';' + i
    key = key[1:]
    content_model.author=authors1
    content_model.keyword=key
    content_model.abstract=ab
    content_model.title=title
    content_model.issue=date
    content_model.doi=doi
    content_model.country=contory
    content_model.institue=ins
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
    content_model.title=list['Title']
    content_model.pmid=list['PMID']
    content_model.journal = list['Title']

    return content_model

# 解析science_direct 文章详情的json字符串为一个content model对象
def format_scicent_details(detail_str):
    # TODO 解析science_direct的文章详情的json字符串，用于下一步的数据库存贮和序列化
    # TODO detail_str 为None时，构造一个失败结果对象
    #========= 预处理 ==================
    content_model = Content()
    # jsons1 = '{"userAgent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36","abstracts":{"content":[{"#name":"abstract","$":{"xmlns:ce":true,"class":"author","view":"all","id":"d1e1344"},"$$":[{"#name":"section-title","$":{"id":"d1e1345"},"_":"Abstract"},{"#name":"abstract-sec","$":{"view":"all","id":"d1e1347"},"$$":[{"#name":"simple-para","$":{"view":"all","id":"d1e1348"},"$$":[{"#name":"__text__","_":"Hash functions are a key component of many essential applications, ranging from compilers, databases or internet browsers to videogames or network devices. The same reduced set of functions are extensively used and have become “"},{"#name":"italic","_":"standard de facto"},{"#name":"__text__","_":"” since they provide very efficient results in searches over unsorted sets. However, depending on the characteristics of the data being hashed, the overall performance of these non-cryptographic hash functions can vary dramatically, becoming a very common source of performance loss. Hash functions are difficult to design, they are extremely non-linear and counter-intuitive, and relationships among variables are often intricate and obscure. Surprisingly, very little scientific research is devoted to the design and experimental assessment of these widely used functions. In this work, in addition to performing an up-to-date comparison of state-of-the-art hash functions, we propose the use of evolutionary techniques for designing "},{"#name":"italic","_":"“ad hoc”"},{"#name":"__text__","_":" non-cryptographic hash functions. Thus, genetic programming will be used to automatically design a tailor-made hash function that can be continuously evolved if needed, so that it is always adapted to real-world dynamic environments. To validate the proposed approach, we have compared several quality metrics for the generated functions and the most widely used non-cryptographic hash functions across eight different scenarios. The results of the evolved hash functions outperformed those of the non-cryptographic hash functions in most of the cases tested."}]}]}]},{"#name":"abstract","$":{"xmlns:ce":true,"class":"graphical","view":"all","id":"d1e1356"},"$$":[{"#name":"section-title","$":{"id":"d1e1357"},"_":"Graphical abstract"},{"#name":"abstract-sec","$":{"view":"all","id":"d1e1359"},"$$":[{"#name":"simple-para","$":{"view":"all","id":"d1e1360"},"$$":[{"#name":"display","$$":[{"#name":"figure","$":{"id":"dfig1"},"$$":[{"#name":"link","$":{"xmlns:xlink":true,"locator":"fx1","href":"pii:S1568494619300742/fx1","role":"http://data.elsevier.com/vocabulary/ElsevierContentTypes/23.4","id":"d1e1364"}}]}]}]}]}]},{"#name":"abstract","$":{"xmlns:ce":true,"class":"author-highlights","view":"all","id":"d1e1365"},"$$":[{"#name":"section-title","$":{"id":"d1e1366"},"_":"Highlights"},{"#name":"abstract-sec","$":{"view":"all","id":"d1e1368"},"$$":[{"#name":"simple-para","$":{"view":"all","id":"d1e1369"},"$$":[{"#name":"list","$":{"id":"d1e1371"},"$$":[{"#name":"list-item","$":{"id":"d1e1372"},"$$":[{"#name":"label","_":"•"},{"#name":"para","$":{"view":"all","id":"d1e1375"},"_":"We propose an automatic technique able to program tailor-made hash functions."}]},{"#name":"list-item","$":{"id":"d1e1377"},"$$":[{"#name":"label","_":"•"},{"#name":"para","$":{"view":"all","id":"d1e1380"},"_":"Evolved functions dynamically adapt to real-world dynamic environments."}]},{"#name":"list-item","$":{"id":"d1e1382"},"$$":[{"#name":"label","_":"•"},{"#name":"para","$":{"view":"all","id":"d1e1385"},"_":"This approach avoids hashing functions whose performance deteriorates over time."}]},{"#name":"list-item","$":{"id":"d1e1387"},"$$":[{"#name":"label","_":"•"},{"#name":"para","$":{"view":"all","id":"d1e1390"},"_":"Generated functions outperform state-of-the-art hash functions for specific domains."}]}]}]}]}]}],"floats":[],"footnotes":[],"attachments":[{"attachment-eid":"1-s2.0-S1568494619300742-fx1.sml","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/fx1/THUMBNAIL/image/gif/2844d8cca1e85bd8289745343844f4ef/fx1.sml","file-basename":"fx1","abstract-attachment":"true","filename":"fx1.sml","extension":"sml","filesize":"19965","pixel-height":"85","pixel-width":"219","attachment-type":"IMAGE-THUMBNAIL"},{"attachment-eid":"1-s2.0-S1568494619300742-fx1.jpg","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/fx1/DOWNSAMPLED/image/jpeg/d315fded9958148517f75b0d2d5be1c7/fx1.jpg","file-basename":"fx1","abstract-attachment":"true","filename":"fx1.jpg","extension":"jpg","filesize":"48558","pixel-height":"117","pixel-width":"301","attachment-type":"IMAGE-DOWNSAMPLED"},{"attachment-eid":"1-s2.0-S1568494619300742-fx1_lrg.jpg","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/fx1/HIGHRES/image/jpeg/3e8b94c2c54bcb3c937194e97686a48f/fx1_lrg.jpg","file-basename":"fx1","abstract-attachment":"true","filename":"fx1_lrg.jpg","extension":"jpg","filesize":"177156","pixel-height":"519","pixel-width":"1333","attachment-type":"IMAGE-HIGH-RES"}]},"biographies":{"content":[{"#name":"biography","$":{"xmlns:ce":true,"xmlns:aep":true,"xmlns:mml":true,"xmlns:xs":true,"xmlns:xlink":true,"xmlns:xocs":true,"xmlns:tb":true,"xmlns:xsi":true,"xmlns:cals":true,"xmlns:sb":true,"xmlns:sa":true,"xmlns:ja":true,"xmlns":true,"id":"bio1","view":"all"},"$$":[{"#name":"link","$":{"locator":"pic1","type":"simple","href":"pii:S1568494619300742/pic1","role":"http://data.elsevier.com/vocabulary/ElsevierContentTypes/23.4","id":"d1e5408"}},{"#name":"simple-para","$":{"view":"all","id":"d1e5409"},"$$":[{"#name":"bold","_":"Yago Saez"}]}]},{"#name":"biography","$":{"xmlns:ce":true,"xmlns:aep":true,"xmlns:mml":true,"xmlns:xs":true,"xmlns:xlink":true,"xmlns:xocs":true,"xmlns:tb":true,"xmlns:xsi":true,"xmlns:cals":true,"xmlns:sb":true,"xmlns:sa":true,"xmlns:ja":true,"xmlns":true,"id":"bio2","view":"all"},"$$":[{"#name":"link","$":{"locator":"pic2","type":"simple","href":"pii:S1568494619300742/pic2","role":"http://data.elsevier.com/vocabulary/ElsevierContentTypes/23.4","id":"d1e5414"}},{"#name":"simple-para","$":{"view":"all","id":"d1e5415"},"$$":[{"#name":"bold","_":"Cesar Estebanez"}]}]},{"#name":"biography","$":{"xmlns:ce":true,"xmlns:aep":true,"xmlns:mml":true,"xmlns:xs":true,"xmlns:xlink":true,"xmlns:xocs":true,"xmlns:tb":true,"xmlns:xsi":true,"xmlns:cals":true,"xmlns:sb":true,"xmlns:sa":true,"xmlns:ja":true,"xmlns":true,"id":"bio3","view":"all"},"$$":[{"#name":"link","$":{"locator":"pic3","type":"simple","href":"pii:S1568494619300742/pic3","role":"http://data.elsevier.com/vocabulary/ElsevierContentTypes/23.4","id":"d1e5420"}},{"#name":"simple-para","$":{"view":"all","id":"d1e5421"},"$$":[{"#name":"bold","_":"David Quintana"}]}]},{"#name":"biography","$":{"xmlns:ce":true,"xmlns:aep":true,"xmlns:mml":true,"xmlns:xs":true,"xmlns:xlink":true,"xmlns:xocs":true,"xmlns:tb":true,"xmlns:xsi":true,"xmlns:cals":true,"xmlns:sb":true,"xmlns:sa":true,"xmlns:ja":true,"xmlns":true,"id":"bio4","view":"all"},"$$":[{"#name":"link","$":{"locator":"pic4","type":"simple","href":"pii:S1568494619300742/pic4","role":"http://data.elsevier.com/vocabulary/ElsevierContentTypes/23.4","id":"d1e5426"}},{"#name":"simple-para","$":{"view":"all","id":"d1e5427"},"$$":[{"#name":"bold","_":"Pedro Isasi"}]}]}],"floats":[],"footnotes":[],"attachments":[{"attachment-eid":"1-s2.0-S1568494619300742-pic3.sml","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic3/THUMBNAIL/image/gif/c81fdb85007dbbfc98351acc872dbb04/pic3.sml","file-basename":"pic3","filename":"pic3.sml","extension":"sml","filesize":"33508","pixel-height":"164","pixel-width":"140","attachment-type":"IMAGE-THUMBNAIL"},{"attachment-eid":"1-s2.0-S1568494619300742-pic4.sml","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic4/THUMBNAIL/image/gif/4344ddb9b437d32e0fa76ac71d100130/pic4.sml","file-basename":"pic4","filename":"pic4.sml","extension":"sml","filesize":"31120","pixel-height":"164","pixel-width":"140","attachment-type":"IMAGE-THUMBNAIL"},{"attachment-eid":"1-s2.0-S1568494619300742-pic2.sml","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic2/THUMBNAIL/image/gif/4434daa363607dbb0804be4e3906f3e6/pic2.sml","file-basename":"pic2","filename":"pic2.sml","extension":"sml","filesize":"34322","pixel-height":"163","pixel-width":"140","attachment-type":"IMAGE-THUMBNAIL"},{"attachment-eid":"1-s2.0-S1568494619300742-pic1.sml","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic1/THUMBNAIL/image/gif/fc9fd412c73efe4403656d773262bc30/pic1.sml","file-basename":"pic1","filename":"pic1.sml","extension":"sml","filesize":"35563","pixel-height":"164","pixel-width":"140","attachment-type":"IMAGE-THUMBNAIL"},{"attachment-eid":"1-s2.0-S1568494619300742-pic3.jpg","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic3/DOWNSAMPLED/image/jpeg/a352e9644fca399ccc94db409216d389/pic3.jpg","file-basename":"pic3","filename":"pic3.jpg","extension":"jpg","filesize":"41872","pixel-height":"132","pixel-width":"113","attachment-type":"IMAGE-DOWNSAMPLED"},{"attachment-eid":"1-s2.0-S1568494619300742-pic4.jpg","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic4/DOWNSAMPLED/image/jpeg/951418eb09dbc0e0c7009d74384c1a04/pic4.jpg","file-basename":"pic4","filename":"pic4.jpg","extension":"jpg","filesize":"39554","pixel-height":"132","pixel-width":"113","attachment-type":"IMAGE-DOWNSAMPLED"},{"attachment-eid":"1-s2.0-S1568494619300742-pic2.jpg","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic2/DOWNSAMPLED/image/jpeg/18a35b5a018975ac462a7f2e92748da2/pic2.jpg","file-basename":"pic2","filename":"pic2.jpg","extension":"jpg","filesize":"41852","pixel-height":"132","pixel-width":"113","attachment-type":"IMAGE-DOWNSAMPLED"},{"attachment-eid":"1-s2.0-S1568494619300742-pic1.jpg","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic1/DOWNSAMPLED/image/jpeg/6f4ca096e91721a6a82e77f775c9813b/pic1.jpg","file-basename":"pic1","filename":"pic1.jpg","extension":"jpg","filesize":"47328","pixel-height":"132","pixel-width":"113","attachment-type":"IMAGE-DOWNSAMPLED"},{"attachment-eid":"1-s2.0-S1568494619300742-pic3_lrg.jpg","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic3/HIGHRES/image/jpeg/cdc2e9112c6f4f5d5449f3328a4df891/pic3_lrg.jpg","file-basename":"pic3","filename":"pic3_lrg.jpg","extension":"jpg","filesize":"103794","pixel-height":"584","pixel-width":"500","attachment-type":"IMAGE-HIGH-RES"},{"attachment-eid":"1-s2.0-S1568494619300742-pic4_lrg.jpg","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic4/HIGHRES/image/jpeg/df13d2f7c75443bce8f348d73429ecf2/pic4_lrg.jpg","file-basename":"pic4","filename":"pic4_lrg.jpg","extension":"jpg","filesize":"100517","pixel-height":"584","pixel-width":"500","attachment-type":"IMAGE-HIGH-RES"},{"attachment-eid":"1-s2.0-S1568494619300742-pic2_lrg.jpg","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic2/HIGHRES/image/jpeg/b4b5b65fb9ae37bda4fb7fe86b154bc8/pic2_lrg.jpg","file-basename":"pic2","filename":"pic2_lrg.jpg","extension":"jpg","filesize":"95690","pixel-height":"583","pixel-width":"500","attachment-type":"IMAGE-HIGH-RES"},{"attachment-eid":"1-s2.0-S1568494619300742-pic1_lrg.jpg","ucs-locator":"https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619300742/pic1/HIGHRES/image/jpeg/b67e9d1c8ee91b873d07c106b0b4a2ef/pic1_lrg.jpg","file-basename":"pic1","filename":"pic1_lrg.jpg","extension":"jpg","filesize":"136771","pixel-height":"584","pixel-width":"500","attachment-type":"IMAGE-HIGH-RES"}]},"combinedContentItems":{"content":[{"#name":"keywords","$$":[{"#name":"keywords","$":{"xmlns:ce":true,"xmlns:aep":true,"xmlns:xoe":true,"xmlns:mml":true,"xmlns:xs":true,"xmlns:xlink":true,"xmlns:xocs":true,"xmlns:tb":true,"xmlns:xsi":true,"xmlns:cals":true,"xmlns:sb":true,"xmlns:sa":true,"xmlns:ja":true,"xmlns":true,"class":"keyword","view":"all","id":"d1e1392"},"$$":[{"#name":"section-title","$":{"id":"d1e1393"},"_":"Keywords"},{"#name":"keyword","$":{"id":"d1e1395"},"$$":[{"#name":"text","_":"Genetic programming"}]},{"#name":"keyword","$":{"id":"d1e1398"},"$$":[{"#name":"text","_":"Hash functions"}]},{"#name":"keyword","$":{"id":"d1e1401"},"$$":[{"#name":"text","_":"Evolutionary algorithm"}]},{"#name":"keyword","$":{"id":"d1e1404"},"$$":[{"#name":"text","_":"Automated design"}]}]}]}],"floats":[],"footnotes":[],"attachments":[]},"experiments":{},"rawtext":"","authors":{"content":[{"#name":"author-group","$":{"xmlns:ce":true,"id":"d1e1269"},"$$":[{"#name":"author","$":{"id":"au000001","author-id":"S1568494619300742-57c4a6a0d418c9a99516fc2c46ab666c","orcid":"0000-0002-0998-2907","biographyid":"bio1"},"$$":[{"#name":"given-name","_":"Yago"},{"#name":"surname","_":"Saez"},{"#name":"cross-ref","$":{"refid":"aff1","id":"d1e1275"},"$$":[{"#name":"sup","$":{"loc":"post"},"_":"a"}]},{"#name":"cross-ref","$":{"refid":"cor1","id":"d1e1278"},"$$":[{"#name":"sup","$":{"loc":"post"},"_":"⁎"}]},{"#name":"e-address","$":{"xmlns:xlink":true,"id":"ea1","type":"email","href":"mailto:yago.saez@uc3m.es"},"_":"yago.saez@uc3m.es"}]},{"#name":"author","$":{"id":"au000002","author-id":"S1568494619300742-b2d05fdfc6ad6ce5ef4b48c64ef56ac4","biographyid":"bio2"},"$$":[{"#name":"given-name","_":"Cesar"},{"#name":"surname","_":"Estebanez"},{"#name":"cross-ref","$":{"refid":"aff2","id":"d1e1288"},"$$":[{"#name":"sup","$":{"loc":"post"},"_":"b"}]}]},{"#name":"author","$":{"id":"au000003","author-id":"S1568494619300742-b926d967e1bf908ea4678c59a7c76323","biographyid":"bio3"},"$$":[{"#name":"given-name","_":"David"},{"#name":"surname","_":"Quintana"},{"#name":"cross-ref","$":{"refid":"aff1","id":"d1e1296"},"$$":[{"#name":"sup","$":{"loc":"post"},"_":"a"}]},{"#name":"e-address","$":{"xmlns:xlink":true,"id":"ea2","type":"email","href":"mailto:dquintan@inf.uc3m.es"},"_":"dquintan@inf.uc3m.es"}]},{"#name":"author","$":{"id":"au000004","author-id":"S1568494619300742-dc3a876052b13ca16c36d9472e74ba00","biographyid":"bio4"},"$$":[{"#name":"given-name","_":"Pedro"},{"#name":"surname","_":"Isasi"},{"#name":"cross-ref","$":{"refid":"aff1","id":"d1e1306"},"$$":[{"#name":"sup","$":{"loc":"post"},"_":"a"}]},{"#name":"e-address","$":{"xmlns:xlink":true,"id":"ea3","type":"email","href":"mailto:isasi@ia.uc3m.es"},"_":"isasi@ia.uc3m.es"}]},{"#name":"affiliation","$":{"affiliation-id":"S1568494619300742-b0a0df135a0cd4c1700d61c009ed8eab","id":"aff1"},"$$":[{"#name":"label","_":"a"},{"#name":"textfn","_":"Universidad Carlos III de Madrid, Computer Science Department, Avda. de la Universidad 30, Leganes, Madrid, Spain"},{"#name":"affiliation","$":{"xmlns:sa":true},"$$":[{"#name":"organization","_":"Universidad Carlos III de Madrid, Computer Science Department, Avda. de la Universidad 30, Leganes"},{"#name":"city","_":"Madrid"},{"#name":"country","_":"Spain"}]}]},{"#name":"affiliation","$":{"affiliation-id":"S1568494619300742-c1ab2d833b50edbae4fa3191f3332679","id":"aff2"},"$$":[{"#name":"label","_":"b"},{"#name":"textfn","_":"Tuenti, Software Development Department, Madrid, Spain"},{"#name":"affiliation","$":{"xmlns:sa":true},"$$":[{"#name":"organization","_":"Tuenti, Software Development Department"},{"#name":"city","_":"Madrid"},{"#name":"country","_":"Spain"}]}]},{"#name":"correspondence","$":{"id":"cor1"},"$$":[{"#name":"label","_":"⁎"},{"#name":"text","_":"Corresponding author."}]}]}],"floats":[],"footnotes":[],"affiliations":{"aff1":{"#name":"affiliation","$":{"affiliation-id":"S1568494619300742-b0a0df135a0cd4c1700d61c009ed8eab","id":"aff1"},"$$":[{"#name":"label","_":"a"},{"#name":"textfn","_":"Universidad Carlos III de Madrid, Computer Science Department, Avda. de la Universidad 30, Leganes, Madrid, Spain"},{"#name":"affiliation","$":{"xmlns:sa":true},"$$":[{"#name":"organization","_":"Universidad Carlos III de Madrid, Computer Science Department, Avda. de la Universidad 30, Leganes"},{"#name":"city","_":"Madrid"},{"#name":"country","_":"Spain"}]}]},"aff2":{"#name":"affiliation","$":{"affiliation-id":"S1568494619300742-c1ab2d833b50edbae4fa3191f3332679","id":"aff2"},"$$":[{"#name":"label","_":"b"},{"#name":"textfn","_":"Tuenti, Software Development Department, Madrid, Spain"},{"#name":"affiliation","$":{"xmlns:sa":true},"$$":[{"#name":"organization","_":"Tuenti, Software Development Department"},{"#name":"city","_":"Madrid"},{"#name":"country","_":"Spain"}]}]}},"correspondences":{"cor1":{"#name":"correspondence","$":{"id":"cor1"},"$$":[{"#name":"label","_":"⁎"},{"#name":"text","_":"Corresponding author."}]}},"attachments":[],"scopusAuthorIds":{},"articles":{}},"body":{},"exam":{},"article":{"publication-content":{"noElsevierLogo":false,"imprintPublisher":{"displayName":"Elsevier","id":"47"},"isSpecialIssue":false,"isSampleIssue":false,"transactionsBlocked":false,"publicationOpenAccess":{"oaStatus":"","oaArticleCount":27,"openArchiveStatus":false,"openArchiveArticleCount":0,"openAccessStartDate":"","oaAllowsAuthorPaid":true},"issue-cover":{"attachment":[{"attachment-eid":"1-s2.0-S1568494619X00046-cov200h.gif","file-basename":"cov200h","extension":"gif","filename":"cov200h.gif","ucs-locator":["https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619X00046/cover/DOWNSAMPLED200/image/gif/2d1556fc8f849beadc5f01d95da7a6ae/cov200h.gif"],"attachment-type":"IMAGE-COVER-H200","filesize":"24789","pixel-height":"200","pixel-width":"150"},{"attachment-eid":"1-s2.0-S1568494619X00046-cov150h.gif","file-basename":"cov150h","extension":"gif","filename":"cov150h.gif","ucs-locator":["https://s3.amazonaws.com/prod-ucs-content-store-us-east/content/pii:S1568494619X00046/cover/DOWNSAMPLED/image/gif/84b3eb09af6ac244de551b3cc030cf40/cov150h.gif"],"attachment-type":"IMAGE-COVER-H150","filesize":"20864","pixel-height":"150","pixel-width":"113"}]},"smallCoverUrl":"https://ars.els-cdn.com/content/image/S15684946.gif","title":"applied-soft-computing","contentTypeCode":"JL","sourceOpenAccess":false,"publicationCoverImageUrl":"https://ars.els-cdn.com/content/image/1-s2.0-S1568494619X00046-cov150h.gif"},"pii":"S1568494619300742","dates":{"Available online":"13 February 2019","Received":"20 March 2018","Revised":["19 December 2018"],"Accepted":"4 February 2019","Publication date":"1 May 2019"},"access":{"openArchive":false,"openAccess":false},"crawlerInformation":{"canCrawlPDFContent":false,"isCrawler":false},"document-references":57,"analyticsMetadata":{"accountId":"68468","accountName":"Beijing Technology & Business University","loginStatus":"anonymous","userId":"5817471"},"cid":"272229","content-family":"serial","copyright-line":"© 2019 Elsevier B.V. All rights reserved.","cover-date-years":["2019"],"cover-date-start":"2019-05-01","cover-date-text":"May 2019","document-subtype":"fla","document-type":"article","entitledToken":"CA02E7C40F5458C9839003962B67D798E3F4A117FC1BE9A9C29E9F9CD5A52D9FD48A56DEEA17C39C","eid":"1-s2.0-S1568494619300742","doi":"10.1016/j.asoc.2019.02.014","first-fp":"58","hub-eid":"1-s2.0-S1568494619X00046","issuePii":"S1568494619X00046","item-weight":"FULL-TEXT","language":"en","last-lp":"69","last-author":{"#name":"last-author","$":{"xmlns:dm":true},"$$":[{"#name":"author","$":{"xmlns:ce":true,"id":"au000004","author-id":"S1568494619300742-dc3a876052b13ca16c36d9472e74ba00","biographyid":"bio4"},"$$":[{"#name":"given-name","_":"Pedro"},{"#name":"surname","_":"Isasi"},{"#name":"cross-ref","$":{"refid":"aff1","id":"d1e1306"},"$$":[{"#name":"sup","$":{"loc":"post"},"_":"a"}]},{"#name":"e-address","$":{"xmlns:xlink":true,"id":"ea3","type":"email","href":"mailto:isasi@ia.uc3m.es"},"_":"isasi@ia.uc3m.es"}]}]},"normalized-first-auth-initial":"Y","normalized-first-auth-surname":"SAEZ","pages":[{"last-page":"69","first-page":"58"}],"self-archiving":{"#name":"self-archiving","$":{"xmlns:xocs":true},"$$":[{"#name":"sa-start-date","_":"2021-02-19T00:00:00.000Z"},{"#name":"sa-user-license","_":"http://creativecommons.org/licenses/by-nc-nd/4.0/"}]},"srctitle":"Applied Soft Computing","suppl":"C","timestamp":"2019-04-18T07:03:17.01448Z","title":{"content":[{"#name":"title","$":{"xmlns:ce":true,"id":"d1e1266"},"_":"Evolutionary hash functions for specific domains"}],"floats":[],"footnotes":[],"attachments":[]},"vol-first":"78","vol-iss-suppl-text":"Volume 78","userSettings":{"forceAbstract":false,"creditCardPurchaseAllowed":true,"blockFullTextForAnonymousAccess":false,"disableWholeIssueDownload":false,"preventTransactionalAccess":false,"preventDocumentDelivery":true},"contentType":"JL","crossmark":true,"issn":"15684946","issn-primary-formatted":"1568-4946","useEnhancedReader":false,"isCorpReq":false,"pdfDownload":{"linkType":"DOWNLOAD","linkToPdf":"/science/article/pii/S1568494619300742/pdfft?md5=0723b7e9c0b9704228dffd1ede382641&pid=1-s2.0-S1568494619300742-main.pdf","isPdfFullText":false,"fileName":"1-s2.0-S1568494619300742-main.pdf"},"pdfUrlForCrawlers":"https://www.sciencedirect.com/science/article/pii/S1568494619300742/pdfft?md5=0723b7e9c0b9704228dffd1ede382641&pid=1-s2.0-S1568494619300742-main.pdf","indexTag":true,"volRange":"78","issRange":"","freeHtmlGiven":false,"userProfile":{"departmentName":"IP_Beijing Technology & Business University","accessType":"IPRANGE","accountId":"68468","webUserId":"5817471","accountName":"Beijing Technology & Business University","departmentId":"102532","userType":"NORMAL","hasMultipleOrganizations":false},"entitlementReason":"package","articleEntitlement":{"entitled":true,"usageInfo":"(5817471,U|102532,D|68468,A|993,S|34,P|2,PL)(SDFE,CON|846d553827b9e84fde3b24a5db6d8f0a036cgxrqa,SSO|ANON_IP,ACCESS_TYPE)"},"aipType":"none","hasChorus":false,"downloadFullIssue":true,"headerConfig":{"helpUrl":"https://service.elsevier.com/app/home/supporthub/sciencedirect/","contactUrl":"https://service.elsevier.com/app/contact/supporthub/sciencedirect/","userName":"","userEmail":"","orgName":"Beijing Technology & Business University","webUserId":"5817471","libraryBanner":{},"shib_regUrl":"","tick_regUrl":"","recentInstitutions":[],"canActivatePersonalization":false,"hasMultiOrg":false,"userType":"IPRANGE","allowCart":true,"environment":"prod"},"titleString":"Evolutionary hash functions for specific domains","onAbstractWhitelist":false,"isAbstract":false,"isContentVisible":false,"ajaxLinks":{"citingArticles":true,"references":true,"referredToBy":true,"toc":true,"body":true,"recommendations":true}},"specialIssueArticles":{},"recommendations":{},"entitledRecommendations":{"openOnPageLoad":false,"isOpen":false,"articles":[],"selected":[],"currentPage":1,"totalPages":1},"citingArticles":{},"workspace":{"isOpen":false},"crossMark":{"isOpen":false},"userIdentity":{},"refersTo":{},"referredToBy":{},"downloadIssue":{"openOnPageLoad":false,"isOpen":false,"articles":[],"selected":[]},"references":{},"referenceLinks":{"internal":{},"external":{}},"glossary":{},"relatedContent":{"isModal":false,"isOpenSpecialIssueArticles":false,"isOpenRecommendations":true,"isOpenCitingArticles":false,"citingArticles":[false,false,false],"recommendations":[false,false,false,false,false,false],"specialIssueArticles":[false,false,false]},"banner":{"expanded":false},"transientError":{"isOpen":false},"tableOfContents":{"showEntitledTocLinks":true},"chapters":{"toc":[],"isLoading":false},"enrichedContent":{"tableOfContents":false,"researchData":{"hasResearchData":false,"dataProfile":{},"openData":{},"mendeleyData":{},"databaseLinking":{}},"geospatialData":{"attachments":[]},"interactiveCaseInsights":{},"virtualMicroscope":{}},"metrics":{"isOpen":true},"signOut":{"isOpen":false},"issueNavigation":{"previous":{},"next":{}},"tail":{},"linkingHubLinks":[],"signInFromEmail":{"isOpen":false},"clinicalKey":{},"accessOptions":{},"changeViewLinks":{"showFullTextLink":false,"showAbstractLink":false}}'
    jsons1 = detail_str
    content_model=dejson(jsons1,content_model)
    return content_model


# 解析pubmed的xml为一个content model对象
def format_pubmed_xml(xml_str):
    # TODO 解析pubmed的xml为一个model对象，用于下一步的数据库存贮和序列化
    # TODO 当xml_str 为None时，构造一个失败结果对象
    # with open('./data/29031869.xml','r', encoding='utf-8') as f:
    #     xml_str = f.read()

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

            keywords += kw_ele.text + '\n'
            if list == 'Year':
                break
        # print(keywords)
        value.append(keywords[:-1])
    list = list_dic(content, value)
    a = list['ForeName'].split('\n')
    b = list['LastName'].split('\n')
    author = ''
    for p in range(len(a)):
        author += a[p] + b[p] + ','
    list['Author'] = author[:-1]
    # print(list)
    content_model=add(list,content_model)
    return content_model

def is_in_black_list(article_id):
    #TODO 判断是否在黑名单
    return False

def is_deleted(article_id):
    #TODO 判断是否被删除
    return False

if __name__ == '__main__':
    print(format_pubmed_xml('aa').author)
    print(format_scicent_details('aa').abstract)
    pass
