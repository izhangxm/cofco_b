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
from multiprocessing import Process, Lock
from multiprocessing import Queue as ProcessQueen
from multiprocessing.sharedctypes import Value
import threading
import re
import time
import random
from requests.exceptions import ConnectionError, ProxyError
from cofcoAPP.spiders import SPIDERS_STATUS, logger
from cofcoAPP.heplers.SessionHelper import SessionHelper
from cofcoAPP.heplers import ContentHelper, HeadersHelper
from cofcoAPP.heplers import getFTime
from cofcoAPP import spiders

# 任务生成爬虫
class _pubmedIDWorker(Process):
    def __init__(self, kw_id, name=None,thread_num=4):
        Process.__init__(self)
        self.kw_id = kw_id
        self.name = name

        self.thread_num = thread_num
        self.threads = []
        self.pages_queen = ProcessQueen(maxsize=-1)  # 页码queen
        # 获得查询字符串

    class _worker(threading.Thread):
        def __init__(self, kw_id, name=None, pages_queen=None, ids_sessionHelper=None):
            threading.Thread.__init__(self)
            self.kw_id = kw_id
            self.manager = SPIDERS_STATUS[kw_id]
            self.pages_queen = pages_queen
            self.ids_queen = self.manager.ids_queen
            self.ids_sessionHelper = ids_sessionHelper
            self.name = name

            self.data = {
                "EntrezSystem2.PEntrez.PubMed.Pubmed_PageController.PreviousPageName": "results",
                "EntrezSystem2.PEntrez.DbConnector.Db": "pubmed",
                "EntrezSystem2.PEntrez.DbConnector.LastDb": "pubmed",
                "EntrezSystem2.PEntrez.DbConnector.Cmd": "PageChanged",
                "EntrezSystem2.PEntrez.DbConnector.Term": "((12) AND 123) AND 123",
                "CollectionStartIndex": "1",
                "CitationManagerStartIndex": "1",
                "CitationManagerCustomRange": "false",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_Facets.FacetsUrlFrag": "filters%3D",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_Facets.FacetSubmitted": "false",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.sPresentation": "docsum",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.sSort": "none",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.FFormat": "docsum",
                "email_format": "docsum",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.FileFormat": "docsum",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.LastPresentation": "docsum",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.Presentation": "docsum",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_Pager.cPage": "0",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.email_count": "200",
                "email_start": "201",
                "email_address": "",
                "email_subj": "hash+-+PubMed",
                "email_add_text": "",
                "EmailCheck1": "",
                "EmailCheck2": "",
                "citman_count": "200",
                "citman_start": "201",
                "term": "((12) AND 123) AND 123 ",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_ResultsController.ResultCount": "835",
                # "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.EmailHID": "1DkeCYsVvJ14WRSPyel6ij47CPDpKOEE4Tbso3B73KOfYTLrIP_IKZLhDL29CTado55erh-4bm3qGO0p2KLNJJK3ZHDNJ-9g-v",
                # "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.TimelineAdPlaceHolder.BlobID": "NCID_1_252738735_130.14.18.48_9001_1556611162_561033717_0MetA0_S_MegaStore_F_1",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.PrevPageSize": "200",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.LastPageSize": "200",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.sPageSize": "200",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_PageController.SpecialPageName": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_Facets.BMFacets": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.FSort": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.email_sort": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.Sort": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.LastSort": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.FileSort": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.Format": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.LastFormat": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.PrevPresentation": "docsum",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.PrevSort": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_ResultsController.RunLastQuery": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.EmailReport": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.EmailFormat": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.EmailCount": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.EmailStart": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.EmailSort": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.Email": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.EmailSubject": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.EmailText": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.EmailQueryKey": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.QueryDescription": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.Key": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.Answer": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.Holding": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.HoldingFft": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.HoldingNdiSet": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.OToolValue": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.EmailTab.SubjectList": "",
                "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.TimelineAdPlaceHolder.CurrTimelineYear": "",
                "EntrezSystem2.PEntrez.DbConnector.LastTabCmd": "",
                "EntrezSystem2.PEntrez.DbConnector.IdsFromResult": "",
                "EntrezSystem2.PEntrez.DbConnector.LastIdsFromResult": "",
                "EntrezSystem2.PEntrez.DbConnector.LinkName": "",
                "EntrezSystem2.PEntrez.DbConnector.LinkReadableName": "",
                "EntrezSystem2.PEntrez.DbConnector.LinkSrcDb": "",
                "EntrezSystem2.PEntrez.DbConnector.TabCmd": "",
                "EntrezSystem2.PEntrez.DbConnector.QueryKey": "",
                "p%24a": "EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_Pager.Page",
                "p%24l": "EntrezSystem2",
                "p%24st": "pubmed",
            }

        # 获得查询字符串
        def get_kw_query_str(self, kw_id):
            # TODO 根据kw_id，获取当前爬虫的查询字符串
            return 'hash'

        # 新建session, 并寻找 lastQueryKey 和 page_num
        def _updateSpiderInfo(self):
            retry_times = 1
            while retry_times <= spiders.ids_max_retry_times:  # 最多重试次数
                try:
                    logger.log(user=self.name, tag='INFO', info='Trying to get lastQueryKey...:' + str(retry_times),screen=True)
                    # 更新会话
                    self.ids_sessionHelper = SessionHelper(header_fun=HeadersHelper.pubmed_ids_headers)
                    query_str = self.get_kw_query_str(self.kw_id)
                    response = self.ids_sessionHelper.get(url='https://www.ncbi.nlm.nih.gov/pubmed/?term=' + query_str)
                    lastQueryKey_p = re.compile('<input name="EntrezSystem2\.PEntrez\.DbConnector\.lastQueryKey"[\s\S]*?value="([\d])+"',
                        re.I | re.M)
                    r = re.search(lastQueryKey_p, response.text)
                    if not r:
                        print('Cant find the lastQueryKey')
                        raise Exception('Cant find the lastQueryKey')
                    self.ids_sessionHelper.lastQueryKey = r.group(1)
                    return
                except Exception as e:
                    logger.log(user=self.name, tag='ERROR', info=e, screen=True)
                    if not isinstance(e, ProxyError):
                        retry_times += 1

        def _get_page_Num(self, ids_sessionHelper=None):
            retry_times = 1
            while retry_times <= spiders.ids_max_retry_times:  # 最多重试次数
                try:
                    logger.log(user=self.name, tag='INFO', info='Trying to get pageNum ...:' + str(retry_times), screen=True)
                    if not ids_sessionHelper:
                        ids_sessionHelper = SessionHelper(header_fun=HeadersHelper.pubmed_ids_headers)
                    query_str = self.get_kw_query_str(self.kw_id)
                    response = ids_sessionHelper.get(url='https://www.ncbi.nlm.nih.gov/pubmed/?term=' + query_str)
                    lastQueryKey_p = re.compile(
                        '<input name="EntrezSystem2\.PEntrez\.DbConnector\.lastQueryKey"[\s\S]*?value="([\d])+"',
                        re.I | re.M)
                    r = re.search(lastQueryKey_p, response.text)
                    if not r:
                        print('Cant find the lastQueryKey')
                        raise Exception('Cant find the lastQueryKey')
                    ids_sessionHelper.lastQueryKey = r.group(1)
                    self.data["EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_Pager.CurrPage"] = 1
                    self.data["EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.PageSize"] = 200
                    self.data["EntrezSystem2.PEntrez.DbConnector.LastQueryKey"] = int(ids_sessionHelper.lastQueryKey)
                    response = ids_sessionHelper.post('https://www.ncbi.nlm.nih.gov/pubmed', data=self.data)
                    if response.status_code != 200:
                        raise Exception('Connection Failed')
                    ids_p = re.compile('<div class="resc"><dl class="rprtid"><dt>PMID:</dt> <dd>([\d]+)</dd>')
                    ids_list = re.findall(ids_p, response.text)
                    page_num_p = re.compile('Pubmed_Pager.cPage"\sid="pageno"[\s\S]*?last="([\d]+)"', re.I | re.M)
                    r = re.search(page_num_p, response.text)
                    if not r:
                        if len(ids_list) == 0:
                            raise Exception('Cant find the page_num')
                        else:
                            p_result = 1
                    else:
                        p_result = r.group(1)
                    page_num = p_result
                    self.manager.page_Num.value = page_num
                    return page_num, ids_sessionHelper
                except Exception as e:
                    ids_sessionHelper = SessionHelper(header_fun=HeadersHelper.science_headers)
                    logger.log(user=self.name, tag='ERROR', info=e, screen=True)
                    if not isinstance(e, ProxyError):
                        retry_times += 1
            return -1, None

        def run(self):
            page_size = 200
            if not self.ids_sessionHelper:
                self._updateSpiderInfo()  # 更换Helper

            while True:
                # 检查是否被暂停
                if self.manager.idsP_status.value == 2:
                    time.sleep(1)  # 歇息一秒，继续检查
                    continue

                # 检查是否任务是否完成
                if self.manager.idsP_status.value == 3:
                    time.sleep(1)  # 歇息一秒，继续检查
                    continue

                # 检查是否时被终止
                if self.manager.idsP_status.value == 4:
                    break

                task_info = None
                try:
                    task_info = self.pages_queen.get(timeout=1)
                    currPage = task_info['currPage']
                    retry_times = task_info['retry_times']
                    if (retry_times >= spiders.ids_max_retry_times):
                        raise Exception("%s: retry_times=%d! This id is labeled as FAILED!" % (currPage, spiders.ids_max_retry_times))
                    self.data["EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_Pager.CurrPage"] = currPage
                    self.data["EntrezSystem2.PEntrez.PubMed.Pubmed_ResultsPanel.Pubmed_DisplayBar.PageSize"] = page_size
                    self.data["EntrezSystem2.PEntrez.DbConnector.LastQueryKey"] = int(self.ids_sessionHelper.lastQueryKey)
                    response = self.ids_sessionHelper.post('https://www.ncbi.nlm.nih.gov/pubmed', data=self.data)
                    if response.status_code != 200:
                        raise Exception('Connection Failed')
                    ids_p = re.compile('<div class="resc"><dl class="rprtid"><dt>PMID:</dt> <dd>([\d]+)</dd>')
                    ids_list = re.findall(ids_p, response.text)
                    for pubmed_id in ids_list:
                        self.ids_queen.put({'id': pubmed_id, 'retry_times': 0})
                        self.manager.update_ids_qsize(1)
                    self.manager.update_finished_page_Num()
                    logger.log(user=self.name, tag='INFO', info=self.manager.ids_queen_size.value, screen=True)
                except Exception as e:
                    # 判断是否完成
                    finished_page_Num = self.manager.finished_page_Num.value
                    failed_page_Num = self.manager.failed_page_Num.value
                    page_Num = self.manager.page_Num.value

                    if finished_page_Num + failed_page_Num == page_Num:
                        self.manager.idsP_status.value = 3  # 将状态置为已完成
                        continue
                    # 失败后的任务重新放入任务队列，并重新尝试
                    if task_info:
                        retry_times = task_info['retry_times']
                        if (retry_times < spiders.ids_max_retry_times):
                            if not isinstance(e, ProxyError):
                                task_info['retry_times'] += 1
                            self.pages_queen.put(task_info)
                        else:  # 该任务确认已经失败，进行一些后续操作
                            self.manager.update_failed_page_Num()
                        logger.log(user=self.name, tag='ERROR', info=e, screen=True)
                    else:
                        pass
                        # logger.log(user=self.name, tag='INFO', info='Waiting...', screen=False)
                    self._updateSpiderInfo()  # 更换Helper

    def run(self):
        #获取页码
        ids_sessionHelper = SessionHelper(header_fun=HeadersHelper.pubmed_ids_headers)
        page_worker = self._worker(self.kw_id, name="%s %s" % (self.name, 'PAGE_THREAD'),ids_sessionHelper=ids_sessionHelper)
        page_Num, ids_sessionHelper = page_worker._get_page_Num()
        if page_Num == -1:
            page_worker.manager.idsP_status.value = -2  # 任务失败
            self.terminate() #结束进程
            return #结束进程

        del page_worker

        for cur_p in range(page_Num):
            self.pages_queen.put({'currPage':(cur_p+1),'retry_times':0})

        for i in range(self.thread_num):
            name = "%s %s-%02d" % (self.name, 'THREAD', i + 1)
            dt = self._worker(kw_id=self.kw_id, name=name, pages_queen=self.pages_queen, ids_sessionHelper=ids_sessionHelper)
            dt.start()
            self.threads.append(dt)
        # 合并到父进程
        for t in self.threads:
            t.join()

# 根据pubmed_id爬取文章内容，每个进程有好几个线程
class _pubmedContendWorker(Process):
    def __init__(self, kw_id, name=None, thread_num=8):
        Process.__init__(self)
        self.kw_id = kw_id
        self.name = name
        self.thread_num = thread_num
        self.threads = []

    class _worker(threading.Thread):
        def __init__(self, kw_id, name=None):
            threading.Thread.__init__(self)
            self.name = name
            self.kw_id = kw_id
            if kw_id:
                self.manager = SPIDERS_STATUS[kw_id]
                self.ids_queen = self.manager.ids_queen

        def get_raw_content(self, article_id, content_sessionHelper=None, max_retry_times=3):
            sessionHelper = content_sessionHelper
            retry_times = 1
            while retry_times <= max_retry_times:  # 最多重试次数
                try:
                    if not content_sessionHelper:
                        sessionHelper = SessionHelper(header_fun=HeadersHelper.pubmed_content_headers)
                    xml_rsp = sessionHelper.get('https://www.ncbi.nlm.nih.gov/pubmed/' + article_id + '?report=xml&format=text')
                    if xml_rsp.status_code != 200:
                        raise Exception('Connection Failed')
                    xml_str = xml_rsp.text
                    return xml_str
                except Exception as e:
                    if not isinstance(e, ProxyError):
                        retry_times += 1
                    time.sleep(1.0 * random.randrange(1, 200) / 1000)  # 休息一下

        def run(self):
            while True:
                # 检查是否被暂停
                if self.manager.contentP_status.value == 2:  # 任务被暂停
                    time.sleep(1)  # 歇息一秒，继续检查
                    continue

                # 检查是否任务是否完成
                if self.manager.contentP_status.value == 3:
                    time.sleep(1)  # 歇息一秒，继续检查
                    continue

                # 检查是否时被终止
                if self.manager.contentP_status.value == 4:
                    break

                task_info = None
                try:
                    task_info = self.ids_queen.get(timeout=1)
                    pubmed_id = task_info['id']
                    retry_times = task_info['retry_times']
                    if(retry_times>=5):
                        raise Exception(pubmed_id + ': retry_times>=5! This id is labeled as FAILED!')

                    if ContentHelper.is_in_black_list(pubmed_id): # 判断是否在黑名单当中
                        continue
                    # =============================================================================================
                    self.content_sessionHelper = SessionHelper(header_fun=HeadersHelper.pubmed_content_headers)
                    xml_str = self.get_raw_content(article_id=pubmed_id, content_sessionHelper=self.content_sessionHelper,max_retry_times=1)
                    # content_model = ContentSerivice.format_pubmed_xml(xml_str)
                    # TODO 存贮到数据库
                    # content_model.save()
                    # =============================================================================================
                    self.manager.update_finish()
                    info = "%s/%s" % (self.manager.finished_num.value, self.manager.ids_queen_size.value)
                    logger.log(user=self.name, tag='INFO', info=info, screen=True)
                except Exception as e:
                    # 判断是否完成
                    finished_num = self.manager.finished_num.value
                    failed_num = self.manager.failed_num.value
                    ids_queen_size = self.manager.ids_queen_size.value
                    idsP_status = self.manager.idsP_status.value
                    if (idsP_status == -2) or (finished_num + failed_num == ids_queen_size and idsP_status == 3):
                        self.manager.contentP_status.value = 3  # 将状态置为已完成
                        continue
                    # 失败后的任务重新放入任务队列，并重新尝试
                    if task_info:
                        retry_times = task_info['retry_times']
                        if (retry_times < 5):
                            if not isinstance(e, ProxyError):
                                task_info['retry_times'] += 1
                            self.ids_queen.put(task_info)
                        else: # 该任务确认已经失败，进行一些后续操作
                            self.manager.update_failed()
                            # content_model = ContentSerivice.format_pubmed_xml(None)
                            # TODO 存贮到数据库
                            # content_model.save()
                        logger.log(user=self.name, tag='ERROR', info=e, screen=True)
                    else:
                        pass
                        # logger.log(user=self.name, tag='INFO', info='Waiting...', screen=True)
                    time.sleep(1.0 * random.randrange(1, 1000) / 1000)  # 休息一下

    def run(self):
        for i in range(self.thread_num):
            name = "%s %s-%02d" % (self.name, 'THREAD', i + 1)
            dt = self._worker(kw_id=self.kw_id, name=name)
            dt.start()
            self.threads.append(dt)
        # 合并到父进程
        for t in self.threads:
            t.join()


# 爬虫对象
class SpiderManagerForPubmed(object):
    def __init__(self, ids_thread_num=4, content_process_num=2, content_thread_num=8, **kwargs):
        # 爬虫的状态信息
        self.kw_id = kwargs['kw_id']
        if SPIDERS_STATUS.get(self.kw_id):
            raise Exception('current kw has been existed')
        self.TYPE = 'PUBMED_SPIDER'
        self.id_process = None  # ID进程对象
        self.content_process = []  # Content进程对象
        self.ids_thread_num = ids_thread_num  # ids线程个数
        self.content_process_num = content_process_num  # Content进程个数
        self.content_thread_num = content_thread_num  # 每个Content进程的线程个数

        self.ids_queen = ProcessQueen(maxsize=-1)  # 待爬取的文章ID列表，是个队列
        self.page_Num = Value('i', 0, lock=True)  # 页数
        self.finished_page_Num = Value('i', 0, lock=True)  # 页数
        self.finished_page_Num_locker = Lock()  # Lock()
        self.failed_page_Num = Value('i', 0, lock=True)  # 页数
        self.failed_page_Num_locker = Lock()  # Lock()


        self.ids_queen_size = Value('i', 0, lock=True)  # 由于qsize的不准确性以及mac平台未实现qsize函数，因此自己实现
        self.ids_queen_size_locker = Lock()  # Lock()
        # self.total_num = Value('i', 0, lock=True)  # 这个数字应该等于pubmed_ids的长度[经过测试，这个也可能不同]
        self.finished_num = Value('i', 0, lock=True)  # 已完成的爬取
        self.finished_num_locker = Lock()  # 已完成的爬取

        self.failed_num = Value('i', 0, lock=True)  # 失败的爬取
        self.failed_num_locker = Lock()  # 失败的爬取

        self.status = Value('i', -1, lock=True)  # 爬虫状态类型为整数, -1:未初始化,0:未运行,1:正在运行，2:暂停, 3:运行完成，4:被终止，5:混合状态
        self.idsP_status = Value('i', -1, lock=True)  # 爬虫状态类型为整数, -1:未初始化,0:未运行,1:正在运行，2:暂停, 3:运行完成，4:被终止，
        self.contentP_status = Value('i', -1, lock=True)  # 爬虫状态类型为整数, -1:未初始化,0:未运行,1:正在运行，2:暂停, 3:运行完成，4:被终止，

        self.create_user_id = kwargs['create_user_id']  # 创建人的ID
        self.create_user_name = kwargs['create_user_name']  # 创建人名称
        self.create_time = getFTime()  # 爬虫创建时间
        self.start_time = None  # 爬虫启动时间

        SPIDERS_STATUS[self.kw_id] = self

    def update_finish(self):
        # 完成数目+1
        self.finished_num_locker.acquire()
        self.finished_num.value += 1
        self.finished_num_locker.release()

    def update_failed(self):
        # 完成数目+1
        self.failed_num_locker.acquire()
        self.failed_num.value += 1
        self.failed_num_locker.release()

    def update_ids_qsize(self, add_N=1):
        self.ids_queen_size_locker.acquire()
        self.ids_queen_size.value += add_N
        self.ids_queen_size_locker.release()

    def update_finished_page_Num(self):
        self.finished_page_Num_locker.acquire()
        self.finished_page_Num.value += 1
        self.finished_page_Num_locker.release()

    def update_failed_page_Num(self):
        self.failed_page_Num_locker.acquire()
        self.failed_page_Num.value += 1
        self.failed_page_Num_locker.release()


    def start(self):
        self.start_time = getFTime()
        common_tag = "KWID=%03d uid=%s uname=%s" % (int(self.kw_id), self.create_user_id, self.create_user_name)
        self.status.value = 1  # 将状态置为开始

        # 启动获取pubmedID的进程
        id_worker = _pubmedIDWorker(kw_id=self.kw_id, name='%s PUBMED_IDS_PROCESS-MAIN' % common_tag,thread_num=self.ids_thread_num)
        id_worker.start()
        self.id_process = id_worker
        self.idsP_status.value =1

        # 启动获取 content 的进程
        for i in range(self.content_process_num):
            name = '%s PUBMED_CONTEND_PROCESS-%02d' % (common_tag, int(i + 1))
            content_worker = _pubmedContendWorker(kw_id=self.kw_id, name=name)
            content_worker.start()
            self.content_process.append(content_worker)
        self.contentP_status.value = 1

    def getStatus(self):
        if self.idsP_status.value == -2 or self.contentP_status.value == -2:
            self.status.value = -2
        elif self.idsP_status.value == 1 or self.contentP_status.value == 1:
            self.status.value = 1
        elif self.idsP_status.value == 2 and self.contentP_status.value == 2:
            self.status.value = 2
        elif self.idsP_status.value == 3 and self.contentP_status.value == 3:
            self.status.value = 3
        elif self.idsP_status.value == 4 and self.contentP_status.value == 4:
            self.status.value = 4
        else:
            self.status.value = 5
        return self.status.value

    def resume(self, idsP=True, contentP=True):
        error_ = []
        if idsP:
            if self.idsP_status.value != 2:
                error_.append(Exception('IDS process status is invalided'))
            else:
                self.idsP_status.value = 1
        if contentP:
            if self.contentP_status.value != 2:
                error_.append(Exception('Content process status is invalided'))
            else:
                self.contentP_status.value = 1
                self.start_time = getFTime()  # 爬虫启动时间
        self.status.value = self.getStatus()
        return error_

    def pause(self, idsP=True, contentP=True):
        error_ = []
        if idsP:
            if self.idsP_status.value != 1:
                error_.append(Exception('IDS process status is invalided'))
            else:
                self.idsP_status.value = 2
        if contentP:
            if self.contentP_status.value != 1:
                error_.append(Exception('Content process status is invalided'))
            else:
                self.contentP_status.value = 2
        self.status.value = self.getStatus()
        return error_

    def terminate(self, idsP=True, contentP=True):
        error_ = []
        try:
            if idsP:
                self.idsP_status.value = 4
                self.id_process.terminate()  # ids 进程
            if contentP:
                self.contentP_status.value = 4
                for c_process in self.content_process:
                    c_process.terminate()
        except Exception as e:
            error_.append(e)
        self.status.value = self.getStatus()
        return error_

    def delete(self):
        error_ = []
        try:
            SPIDERS_STATUS.pop(self.kw_id, None)
            self.terminate(idsP=True, contentP=True)
        except Exception as e:
            error_.append(e)
        return error_


if __name__ == '__main__':
    sfp = SpiderManagerForPubmed(kw_id='23', content_process_num=2, content_thread_num=16, update_times='12',
                                 create_user_id='uid', create_user_name='uname')
    print(sfp)
    sfp.start()
    print('start successful')

