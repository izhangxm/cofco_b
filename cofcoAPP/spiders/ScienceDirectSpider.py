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
import os
import json
from requests.exceptions import ConnectionError, ProxyError
from cofco_b.settings import BASE_DIR
from cofcoAPP.spiders import SPIDERS_STATUS, logger
from cofcoAPP.heplers.SessionHelper import SessionHelper
from cofcoAPP.heplers import ContentHelper, HeadersHelper
from cofcoAPP.heplers import getFTime
from cofcoAPP import spiders
from cofcoAPP.models import SpiderKeyWord,Content
import asyncio
from cofcoAPP.models import get_json_model

# 任务生成爬虫
class _scienceIDWorker(Process):
    def __init__(self, kw_id, name=None,thread_num=4, page_size=spiders.default_science_pagesize):
        Process.__init__(self)
        self.kw_id = kw_id
        self.name = name
        self.thread_num = thread_num
        self.threads = []
        self.page_size = page_size
        self.pages_queen = ProcessQueen(maxsize=-1)  # 页码queen

    class _worker(threading.Thread):
        def __init__(self, kw_id, name=None, pages_queen=None, ids_sessionHelper=None, page_size=spiders.default_science_pagesize):
            threading.Thread.__init__(self)
            self.kw_id = kw_id
            self.manager = SPIDERS_STATUS[kw_id]
            self.ids_queen = self.manager.ids_queen
            self.name = name
            self.page_size = page_size
            self.pages_queen = pages_queen
            self.ids_queen = self.manager.ids_queen
            self.ids_sessionHelper = ids_sessionHelper

        # 获得查询字符串
        def get_kw_query_str(self, kw_id):
            try:
                kw_ = SpiderKeyWord.objects.filter(id=kw_id).values()[0]
                query_str = ""
                for key,value in json.loads(kw_['value']).items():
                    if value == '':
                        continue
                    if len(query_str) > 0:
                        query_str += '&'
                    if key == 'articleTypes':
                        value = " ".join(value.keys())
                    query_str += "%s=%s" %(key,value)
                logger.log(user=self.name, tag='INFO', info="query_str:%s !" % query_str, screen=True)
                return query_str
            except Exception as e:
                raise Exception('Error: unable to parse the kw_id! %s' % e)

        def _get_page_Num(self, ids_sessionHelper=None):
            retry_times = 1
            while retry_times <= spiders.ids_max_retry_times:  # 最多重试次数
                try:
                    logger.log(user=self.name, tag='INFO', info='Trying to get pageNum ...:' + str(retry_times), screen=True)
                    if not ids_sessionHelper:
                        ids_sessionHelper = SessionHelper(header_fun=HeadersHelper.science_headers)
                    query_str = self.get_kw_query_str(self.kw_id)
                    offset = 0
                    query_str = "%s&show=%d&sortBy=relevance&offset=%d" % (query_str, self.page_size, offset)
                    response = ids_sessionHelper.get('https://www.sciencedirect.com/search?' + query_str)
                    if response.status_code != 200:
                        raise Exception('Connection Failed')
                    content = response.text.encode().decode('unicode_escape')
                    page_num_p = re.compile('Page\s[\d]+\sof\s(\d+)</li>', re.I | re.M)
                    r = re.search(page_num_p, content)
                    page_num = int(r.group(1)) if r else 0
                    self.manager.page_Num.value = page_num
                    logger.log(user=self.name, tag='INFO', info='Get pageNum:%d successfully.' % page_num, screen=True)
                    return page_num
                except Exception as e:
                    logger.log(user=self.name, tag='ERROR', info=e, screen=True)
                    if not isinstance(e, ProxyError):
                        retry_times += 1
                    ids_sessionHelper = SessionHelper(header_fun=HeadersHelper.science_headers)
                    time.sleep(1.0 * random.randrange(1, 1000) / 1000)  # 休息一下
            return -1

        def run(self):
            asyncio.set_event_loop(asyncio.new_event_loop())
            if not self.ids_sessionHelper:
                self.ids_sessionHelper = SessionHelper(header_fun=HeadersHelper.science_headers)
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
                        raise Exception("%s: retry_times=%d! This id is labeled as FAILED!" % (
                        currPage, spiders.ids_max_retry_times))

                    query_str = self.get_kw_query_str(self.kw_id)
                    offset = (currPage - 1) * self.page_size
                    query_str = "%s&offset=%d&show=%d" % (query_str, offset, self.page_size)
                    response = self.ids_sessionHelper.get('https://www.sciencedirect.com/search?' + query_str)
                    if response.status_code != 200:
                        raise Exception('Connection Failed')
                    content = response.text.encode().decode('unicode_escape')
                    pii_ids_p = re.compile('"pii":"([\w\d]+)"', re.I | re.M)
                    results = re.findall(pii_ids_p, content)
                    for art_id in results:
                        self.ids_queen.put({'id': art_id, 'retry_times': 0})
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
                        # logger.log(user=self.name, tag='INFO', info='Waiting...', screen=True)
                    self.ids_sessionHelper = SessionHelper(header_fun=HeadersHelper.science_headers)

    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        # 获取页码
        page_worker = self._worker(self.kw_id, name="%s %s" % (self.name, 'PAGE_THREAD'), page_size=self.page_size)
        page_Num = page_worker._get_page_Num()
        if page_Num == -1:
            page_worker.manager.idsP_status.value = -2  # 任务失败
            self.terminate() #结束进程
            return #结束进程

        if page_Num == 0:
            page_worker.manager.idsP_status.value = 3  # 任务完成
            return  # 结束进程

        del page_worker
        for cur_p in range(page_Num):
            self.pages_queen.put({'currPage': (cur_p + 1), 'retry_times': 0})

        for i in range(self.thread_num):
            name = "%s %s-%02d" % (self.name, 'THREAD', i + 1)
            dt = self._worker(kw_id=self.kw_id, name=name, pages_queen=self.pages_queen, page_size=self.page_size)
            dt.start()
            self.threads.append(dt)
        # 合并到父进程
        for t in self.threads:
            t.join()

# 根据article_id爬取文章内容，每个进程有好几个线程
class _scienceContendWorker(Process):
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
            self.sessionHelper = None
            if kw_id:
                self.manager = SPIDERS_STATUS[kw_id]
                self.ids_queen = self.manager.ids_queen

        # 判断是否被 Forbidden 拒绝服务
        def _isBlocked(self,rsp_text):
            r = re.search(re.compile(r'<center><h1>403 Forbidden</h1></center>'),rsp_text)
            return r is not None

        # 当前的内容获取线程应当基于搜索得到的session
        # 并设置好头信息
        def _updateSession(self, ids_max_retry_times=3):
            retry_times = 1
            while retry_times <= ids_max_retry_times:  # 最多重试次数
                try:
                    logger.log(user=self.name, tag='INFO',
                               info='Trying to Update the session!...:' + str(retry_times),
                               screen=True)
                    query_worker = _scienceIDWorker(kw_id=self.kw_id,name='SciContentUS-Process')._worker(kw_id=self.kw_id,name='SciContentUS-Thread')

                    ids_sessionHelper = SessionHelper(header_fun=HeadersHelper.science_headers)
                    query_str = query_worker.get_kw_query_str(self.kw_id)
                    offset = 0
                    query_str = "%s&offset=%d&show=%d" % (query_str, offset, spiders.default_science_pagesize)

                    response = ids_sessionHelper.get('https://www.sciencedirect.com/search?' + query_str)
                    if response.status_code != 200:
                        raise Exception('Connection Failed')

                    rsp_text = response.text.encode().decode('unicode_escape')
                    if self._isBlocked(rsp_text):
                        continue
                    # 设置header: refer
                    headers = {'Referer': query_str, 'Upgrade-Insecure-Requests': '1'}
                    ids_sessionHelper.session.headers.update(headers)
                    self.sessionHelper = ids_sessionHelper

                    logger.log(user=self.name, tag='INFO', info='Update the session successfully.', screen=True)
                    return self.sessionHelper
                except Exception as e:
                    logger.log(user=self.name, tag='ERROR', info=e, screen=True)
                    if not isinstance(e, ProxyError):
                        retry_times += 1
                    time.sleep(1.0 * random.randrange(1, 1000) / 1000)  # 休息一下
            raise Exception('Update the session failed!')

        def _find_details_str(self,rsp_text):
            detail_str_p = re.compile('<script type="application/json" data-iso-key="_0">(\{[\s\S]*?\}\})</script>')
            r = re.search(detail_str_p, rsp_text)
            return r.group(1)

        def get_dict_data_from_link(self,url):
            if(url[-1] == '/'):
                url = url[:-1]
            article_id = url.split('/')[-1]
            rsp_text = self.get_raw_content(article_id=article_id,max_retry_times=3)
            details_str = self._find_details_str(rsp_text)
            content_model = ContentHelper.format_scicent_details(details_str)
            data_dict = get_json_model(content_model)
            data_dict['art_id'] = article_id
            return data_dict

        def get_raw_content(self, article_id, content_sessionHelper=None, max_retry_times=3):
            sessionHelper = content_sessionHelper
            retry_times = 1
            while retry_times <= max_retry_times:  # 最多重试次数
                try:
                    if not content_sessionHelper:
                        sessionHelper = SessionHelper(header_fun=HeadersHelper.science_headers)
                    rsp = sessionHelper.get('https://www.sciencedirect.com/science/article/pii/' + article_id)
                    if rsp.status_code != 200:
                        raise Exception('Connection Failed')
                    return rsp.text
                except Exception as e:
                    if not isinstance(e, ProxyError):
                        retry_times += 1
                    time.sleep(1.0 * random.randrange(1, 200) / 1000)  # 休息一下
            raise Exception('Get %s raw content failed!' % (article_id))

        def run(self):
            asyncio.set_event_loop(asyncio.new_event_loop())
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
                    article_id = str(task_info['id'])
                    retry_times = int(task_info['retry_times'])
                    if (retry_times >= spiders.content_max_retry_times):
                        raise Exception('%s: retry_times>=%d! This id is labeled as FAILED!'%(article_id, spiders.content_max_retry_times))

                    if ContentHelper.is_in_black_list(article_id): # 判断是否在黑名单当中
                        continue

                    if not self.sessionHelper:
                        self._updateSession()  # 更换Helper

                    rsp_text = self.get_raw_content(article_id=article_id, content_sessionHelper=self.sessionHelper,max_retry_times=1)
                    if self._isBlocked(rsp_text): # 如果被forbidden，就放弃当前的session
                        self.sessionHelper = None
                        raise Exception('This session has been blocked!')

                    details_str = self._find_details_str(rsp_text)
                    # =============================================================================================
                    try:
                        content_model = ContentHelper.format_scicent_details(details_str)
                        content_model.status = 0
                        content_model.art_id = article_id
                        content_model.kw_id = int(self.kw_id)
                        content_model.creater = self.manager.create_user_id
                        content_model.project = self.manager.TYPE
                        ContentHelper.content_save(content_model)
                    except Exception as e:
                        txt_path = os.path.join(BASE_DIR,'test/failed_science',article_id+'.txt')
                        with open(txt_path,'w+',encoding='utf-8') as f:
                            f.write(details_str)
                        raise e
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
                    # 任务失败或者正常完成
                    if (idsP_status == -2) or (finished_num + failed_num == ids_queen_size and idsP_status == 3):
                        self.manager.contentP_status.value = 3  # 将状态置为已完成
                        continue
                    # 失败后的任务重新放入任务队列，并重新尝试
                    if task_info:
                        retry_times = task_info['retry_times']
                        if (retry_times < spiders.content_max_retry_times):
                            if not isinstance(e, ProxyError):
                                task_info['retry_times'] += 1
                            self.ids_queen.put(task_info)
                        else: # 该任务确认已经失败，进行一些后续操作
                            self.manager.update_failed()
                            self.manager.failed_ids_queen.put(task_info)
                            # content_model = Content()
                            # content_model.status = -3
                            # content_model.art_id = str(task_info['id'])
                            # content_model.title = '该文章爬取失败'
                            # content_model.kw_id = int(self.kw_id)
                            # content_model.creater = self.manager.create_user_id
                            # content_model.project = self.manager.TYPE
                            # ContentHelper.content_save(content_model)
                        logger.log(user=self.name, tag='ERROR', info=e, screen=True)
                    else:
                        pass
                        # logger.log(user=self.name, tag='INFO', info='Waiting...', screen=True)
                    time.sleep(1.0 * random.randrange(1, 1000) / 1000)  # 休息一下
    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        for i in range(self.thread_num):
            name = "%s %s-%02d" % (self.name, 'THREAD', i + 1)
            dt = self._worker(kw_id=self.kw_id, name=name)
            dt.start()
            self.threads.append(dt)
        # 合并到父进程
        for t in self.threads:
            t.join()


# 爬虫对象
class SpiderManagerForScience(object):
    def __init__(self,ids_thread_num=4, content_process_num=2, content_thread_num=8,page_size=spiders.default_science_pagesize,  **kwargs):
        # 爬虫的状态信息
        self.kw_id = kwargs['kw_id']
        if SPIDERS_STATUS.get(self.kw_id):
            raise Exception('current kw has been existed')
        try:
            kw_json = SpiderKeyWord.objects.filter(id=self.kw_id).values()[0]
            self.kw_name = kw_json['name']
        except Exception as e:
            raise Exception('查询关键词名字失败'+str(e))
        self.TYPE = 'SCIENCE_SPIDER'
        self.id_process = None  # ID进程对象
        self.content_process = []  # Content进程对象
        self.ids_thread_num = ids_thread_num  # ids线程个数
        self.content_process_num = content_process_num  # Content进程个数
        self.content_thread_num = content_thread_num  # 每个Content进程的线程个数

        self.ids_queen = ProcessQueen(maxsize=-1)  # 待爬取的文章ID列表，是个队列
        self.failed_ids_queen = ProcessQueen(maxsize=-1)  # 已失败的文章ID列表，是个队列
        self.page_Num = Value('i', -1, lock=True)  # 页数
        self.page_size = page_size  # 页面大小
        self.finished_page_Num = Value('i', 0, lock=True)  # 页数
        self.finished_page_Num_locker = Lock()  # Lock()
        self.failed_page_Num = Value('i', 0, lock=True)  # 页数
        self.failed_page_Num_locker = Lock()  # Lock()

        self.ids_queen_size = Value('i', 0, lock=True)  # 由于qsize的不准确性以及mac平台未实现qsize函数，因此自己实现
        self.ids_queen_size_locker = Lock()  # Lock()

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

        # 查询相关的信息
        self.lastQueryKey = -1

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
        self.common_tag = "KWID=%03d uid=%s uname=%s" % (int(self.kw_id), self.create_user_id, self.create_user_name)
        self.status.value = 1  # 将状态置为开始

        # 启动获取pubmedID的进程
        id_worker = _scienceIDWorker(kw_id=self.kw_id, name='%s SCIENCE_IDS_PROCESS-MAIN' % self.common_tag, thread_num=self.ids_thread_num, page_size=self.page_size)
        id_worker.start()
        self.id_process = id_worker
        self.idsP_status.value =1

        # 启动获取 content 的进程
        for i in range(self.content_process_num):
            name = '%s SCIENCE_CONTEND_PROCESS-%02d' % (self.common_tag, int(i + 1))
            content_worker = _scienceContendWorker(kw_id=self.kw_id, name=name)
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

    def pause(self,  idsP=True, contentP=True):
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

    def terminate(self,  idsP=True, contentP=True):
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

    def retry(self):
        try:
            for i in range(self.failed_num.value):
                task_info = self.failed_ids_queen.get(timeout=1)
                task_info['retry_times'] = 0
                self.ids_queen.put(task_info)
            self.failed_num.value = 0

            # step1: 先结束content 的进程
            for c_process in self.content_process:
                c_process.terminate()
            self.content_process = []

            # step2: 启动获取 content 的进程
            for i in range(self.content_process_num):
                name = '%s SCIENCE_CONTEND_PROCESS-%02d' % (self.common_tag, int(i + 1))
                content_worker = _scienceContendWorker(kw_id=self.kw_id, name=name)
                content_worker.start()
                self.content_process.append(content_worker)
            self.contentP_status.value = 1

        except Exception as e:
            raise e


if __name__ == '__main__':
    sfp = SpiderManagerForScience(kw_id='23', content_process_num=2, content_thread_num=16, update_times='12', create_user_id='uid', create_user_name='uname')
    sfp.start()
    print('start successful')
