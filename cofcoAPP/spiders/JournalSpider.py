# -*- coding: utf-8 -*-
# !/usr/bin/env python
# coding:utf-8
"""
-------------------------------------------------
   File Name: journal.py
   Description: 处理与影响因子及文章分区相关查询
   Author: shijack
   Date：2018年01月04日
-------------------------------------------------
"""
"""
此爬虫应该定期更新，存到本地数据库，之后直接查询文章分区和影响因子即可
"""

from __future__ import division  # python除法变来变去的，这句必须放开头
import sys
import re
import requests
from lxml import etree
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
import mysql_handler as mh
import agents
import message as msg
import config

journal_name_list = mh.read_journal_name_all()  # 数据
ojournal_name_list = mh.read_ojournal_name_all()  # 读取


def journal_name_wash(journal_name_raw):  # 原始名称清洗（主要针对各种括号和标点、解释、注释）
    re_bracket = re.compile("[\\[\\(](.*?)[\\]\\)]")  # 去处括号解释
    re_explaination = re.compile(" ??[:=].*")  # 去处冒号后的解释
    journal_name = journal_name_raw.replace('&amp;', "&").replace(
        ',', '').replace(".", '')  # &是部分名称中包含的
    journal_name = re_bracket.sub('', journal_name)
    journal_name = re_explaination.sub('', journal_name)
    journal_name = journal_name.upper()  # 清洗过的名称全大写
    msg.msg("journal name", journal_name_raw, "washed",
            journal_name, "debug", msg.display)
    return journal_name


def get_official_name(journal_name_raw, proxy=None):  # 查找杂志的全名，支持模糊查询，只输出最符合的那个
    url = "http://www.letpub.com.cn/journalappAjax.php?querytype=autojournal&term=" + \
          journal_name_raw.replace("&", "%26").replace(" ", "+")
    tries = config.request_dp_tries
    while tries > 0:
        try:
            opener = requests.Session()
            doc = opener.get(url, timeout=20, headers=agents.get_header_jounal()).text
            list = doc.split('},{')  # 获取列表，但是只有最match的被采纳
            journal_name_start = list[0].find("label") + 8
            journal_name_end = list[0].find("\",\"", journal_name_start)
            journal_name = list[0][journal_name_start:journal_name_end]
            journal_name = journal_name.upper()  # 查找到的名字也是全大写
            msg.msg("journal name", journal_name_raw, "web retrieved",
                    journal_name, "debug", msg.display)
            return journal_name
        except Exception, e:
            msg.msg("journal name", journal_name, "web retrieved",
                    "retried", "debug", msg.display)
            msg.msg("journal name", journal_name,
                    "web retrieved", str(e), "error", msg.log)
            tries -= 1
            time.sleep(config.request_refresh_wait)
    else:
        msg.msg("journal name", journal_name, "web retrieved",
                "fail", "error", msg.log, msg.display)
        return ""


def get_journal_info(ojournal_name, proxy=None):  # 查找杂志影响因子、分区, 要求输入精准
    url = "http://www.letpub.com.cn/index.php?page=journalapp&view=search"
    search_str = {
        "searchname": "",
        "searchissn": "",
        "searchfield": "",
        "searchimpactlow": "",
        "searchimpacthigh": "",
        "searchscitype": "",
        "view": "search",
        "searchcategory1": "",
        "searchcategory2": "",
        "searchjcrkind": "",
        "searchopenaccess": "",
        "searchsort": "relevance"}
    search_str["searchname"] = ojournal_name
    tries = config.request_dp_tries
    while tries > 0:
        try:
            opener = requests.Session()
            doc = opener.post(url, timeout=20, data=search_str).text
            selector = etree.HTML(doc.encode("utf-8"))
            journal_detail_element = selector.xpath(
                "//td[@style=\"border:1px #DDD solid; border-collapse:collapse; text-align:left; padding:8px 8px 8px 8px;\"]")
            if len(journal_detail_element):
                impact_factor = journal_detail_element[2].xpath('string(.)')
                publication_zone = journal_detail_element[3].xpath('string(.)')[
                    0]
            else:
                impact_factor = ""
                publication_zone = ""
            msg.msg("journal info", ojournal_name,
                    "web retrieved", "succ", "debug", msg.display)
            return impact_factor, publication_zone
            break
        except Exception, e:
            msg.msg("journal info", ojournal_name, "web retrieved",
                    "retried", "debug", msg.display)
            msg.msg("journal info", ojournal_name,
                    "web retrieved", str(e), "error", msg.log)
            tries -= 1
            time.sleep(config.request_refresh_wait)
    else:
        msg.msg("journal info", ojournal_name, "web retrieved",
                "fail", "error", msg.log, msg.display)
        return "", ""



def journal_detail(journal_name):
    record = mh.read_journal_detail(journal_name)  # 直接试一下
    if record:
        msg.msg("journal record", journal_name, "local retrieved", "succ", "debug", msg.display)
        return record
    else:
        wjournal_name = journal_name_wash(journal_name)  # 清洗过的在正式名里试一下
        record = mh.read_ojournal_detail(wjournal_name)
        if record:
            msg.msg("journal record", journal_name, "local retrieved", "succ", "debug", msg.display)
            return record
        else:
            ojournal_name = get_official_name(wjournal_name)  # 网络正式名在正式名里试一下
            record = mh.read_ojournal_detail(ojournal_name)
            if record:
                msg.msg("journal record", journal_name, "web retrieved", "succ", "debug", msg.display)
                return record
            else:
                journal_info = get_journal_info(ojournal_name)  # 网络正式名在网络查一下
                journal_if = journal_info[0]
                journal_zone = journal_info[1]
                mh.add_journal(journal_name, ojournal_name, journal_if, journal_zone)  # 新杂志储存
                msg.msg("journal record", journal_name, "web retrieved", "succ", "debug", msg.display)
                data = journal_name, ojournal_name, journal_if, journal_zone
                return data


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
            # TODO 根据kw_id，获取当前爬虫的查询字符串，这里应当去除'&offset=0&show=100'
            return 'qs=hash%20image%20aa&sortBy=relevance'

        def _get_page_Num(self, ids_sessionHelper=None):
            retry_times = 1
            while retry_times <= spiders.ids_max_retry_times:  # 最多重试次数
                try:
                    logger.log(user=self.name, tag='INFO', info='Trying to get pageNum ...:' + str(retry_times), screen=True)
                    if not ids_sessionHelper:
                        ids_sessionHelper = SessionHelper(header_fun=HeadersHelper.science_headers)
                    query_str = self.get_kw_query_str(self.kw_id)
                    offset = 0
                    query_str = "%s&offset=%d&show=%d" % (query_str, offset, self.page_size)
                    response = ids_sessionHelper.get('https://www.sciencedirect.com/search?' + query_str)
                    if response.status_code != 200:
                        raise Exception('Connection Failed')
                    content = response.text.encode().decode('unicode_escape')
                    page_num_p = re.compile('<li>Page <!-- -->[\d]+<!-- -->\sof\s<!-- -->([\d]+)</li>', re.I | re.M)
                    r = re.search(page_num_p, content)
                    if not r:
                        raise Exception('Cant find the page_num')
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
        # 获取页码
        page_worker = self._worker(self.kw_id, name="%s %s" % (self.name, 'PAGE_THREAD'), page_size=self.page_size)
        page_Num = page_worker._get_page_Num()
        if page_Num == -1:
            page_worker.manager.idsP_status.value = -2  # 任务失败
            self.terminate() #结束进程
            return #结束进程

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
            if kw_id:
                self.manager = SPIDERS_STATUS[kw_id]
                self.ids_queen = self.manager.ids_queen

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

                    detail_str_p = re.compile('<script type="application/json" data-iso-key="_0">(\{[\s\S]*?\}\})</script>')
                    r = re.search(detail_str_p, rsp.text)

                    return r.group(1)
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
                    article_id = task_info['id']
                    retry_times = task_info['retry_times']
                    if (retry_times >= spiders.content_max_retry_times):
                        raise Exception("%s: retry_times=%d! This id is labeled as FAILED!" % ( article_id, spiders.content_max_retry_times))

                    if ContentHelper.is_in_black_list(article_id): # 判断是否在黑名单当中
                        continue
                    # =============================================================================================
                    self.content_sessionHelper = SessionHelper(header_fun=HeadersHelper.science_headers)
                    details_str = self.get_raw_content(article_id=article_id, content_sessionHelper=self.content_sessionHelper,max_retry_times=1)
                    # content_model = ContentHelper.format_scicent_details(details_str)
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
                    # 任务失败或者正常完成
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
                            # content_model = ContentSerivice.format_scicent_details(None)
                            # TODO 存贮到数据库
                            # content_model.save()
                        logger.log(user=self.name, tag='ERROR', info=e, screen=True)
                    else:
                        pass
                        # logger.log(user=self.name, tag='INFO', info='Waiting...', screen=True)

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
class SpiderManagerForScience(object):
    def __init__(self,ids_thread_num=4, content_process_num=2, content_thread_num=8,page_size=spiders.default_science_pagesize,  **kwargs):
        # 爬虫的状态信息
        self.kw_id = kwargs['kw_id']
        if SPIDERS_STATUS.get(self.kw_id):
            raise Exception('current kw has been existed')
        self.TYPE = 'SCIENCE_SPIDER'
        self.id_process = None  # ID进程对象
        self.content_process = []  # Content进程对象
        self.ids_thread_num = ids_thread_num  # ids线程个数
        self.content_process_num = content_process_num  # Content进程个数
        self.content_thread_num = content_thread_num  # 每个Content进程的线程个数

        self.ids_queen = ProcessQueen(maxsize=-1)  # 待爬取的文章ID列表，是个队列
        self.ids_queen = ProcessQueen(maxsize=-1)  # 待爬取的文章ID列表，是个队列
        self.page_Num = Value('i', 0, lock=True)  # 页数
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
        common_tag = "KWID=%03d uid=%s uname=%s" % (int(self.kw_id), self.create_user_id, self.create_user_name)
        self.status.value = 1  # 将状态置为开始

        # 启动获取pubmedID的进程
        id_worker = _scienceIDWorker(kw_id=self.kw_id, name='%s SCIENCE_IDS_PROCESS-MAIN' % common_tag, thread_num=self.ids_thread_num, page_size=self.page_size)
        id_worker.start()
        self.id_process = id_worker
        self.idsP_status.value =1

        # 启动获取 content 的进程
        for i in range(self.content_process_num):
            name = '%s SCIENCE_CONTEND_PROCESS-%02d' % (common_tag, int(i + 1))
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


if __name__ == '__main__':
    sfp = SpiderManagerForScience(kw_id='23', content_process_num=2, content_thread_num=16, update_times='12', create_user_id='uid', create_user_name='uname')
    sfp.start()
    print('start successful')

if __name__ == '__main__':
    print(journal_detail("nature protocols:"))
