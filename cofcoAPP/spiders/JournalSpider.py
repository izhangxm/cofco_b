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
import os
from multiprocessing import Process, Lock, Manager, Value
from multiprocessing import Queue as ProcessQueen
from ctypes import c_char_p
import threading
import re
import time
import random
from requests.exceptions import ProxyError
from cofco_b.settings import BASE_DIR
from cofcoAPP import heplers
from cofcoAPP.spiders import SPIDERS_STATUS, logger
from cofcoAPP.heplers.SessionHelper import SessionHelper
from cofcoAPP.heplers import HeadersHelper
from cofcoAPP.heplers import getFTime
from cofcoAPP.models import Journal
from cofcoAPP import spiders

# 任务生成爬虫
class _journalIDWorker(Process):
    def __init__(self, kw_id, name=None, thread_num=4):
        Process.__init__(self)
        self.kw_id = kw_id
        self.name = name
        self.thread_num = thread_num
        self.threads = []
        self.cls_queen = ProcessQueen(maxsize=-1)  # 页码queen

    class _worker(threading.Thread):
        def __init__(self, kw_id, name=None, cls_queen=None):
            threading.Thread.__init__(self)
            self.kw_id = kw_id
            self.manager = SPIDERS_STATUS[kw_id]
            self.ids_queen = self.manager.ids_queen
            self.name = name
            self.cls_queen = cls_queen
            self.data = {}

        def _init_data(self):
            rsp = self.manager.page_sessionHelper.get('https://www.fenqubiao.com/Core/CategoryList.aspx')
            re_result = re.findall(r'input type="hidden"\s+name="(\S+?)"[\s\S]*?value="([\s\S]*?)"', rsp.text)
            for ele in re_result:
                self.data[ele[0]] = ele[1]
            self.data['ctl00$ContentPlaceHolder1$ajaxManager'] = 'ctl00$ContentPlaceHolder1$ajaxManager|ctl00$ContentPlaceHolder1$AspNetPager1'
            self.data['_TSM_HiddenField_'] = 'r8mJnfb49_1ZuIQsipsHX-ZDZDri_bTBCAGx3HICehk1'
            self.data['ctl00$ContentPlaceHolder1$dplYear'] = spiders.journal_year
            self.data['ctl00$ContentPlaceHolder1$dplCategoryType'] = '0'
            self.data['ctl00$ContentPlaceHolder1$dplSection'] = '0'
            self.data['ctl00$ContentPlaceHolder1$dplSort'] = '0'
            self.data['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$AspNetPager1'
            self.data['__ASYNCPOST'] = 'true'

        def run(self):
            self.manager.auto_update_session()
            self._init_data()

            while True:
                # 检查是否被暂停
                if self.manager.idsP_status.value == 2:
                    time.sleep(1)  # 歇息一秒，继续检查
                    continue

                # 检查是否任务是否完成
                if self.manager.idsP_status.value == 3:
                    time.sleep(1)  # 歇息一秒，继续检查
                    continue

                # 检查是否任务是否需要输入cookies
                if self.manager.idsP_status.value == 6:
                    time.sleep(1)  # 歇息一秒，继续检查
                    continue

                # 检查是否时被终止
                if self.manager.idsP_status.value == 4:
                    break

                task_info = None
                try:
                    self.manager.idsP_status.value = 1
                    task_info = self.cls_queen.get(timeout=1)
                    cls_name = task_info['cls_name']
                    retry_times = task_info['retry_times']
                    if (retry_times >= spiders.ids_max_retry_times):
                        raise Exception("%s: retry_times=%d! This id is labeled as FAILED!" % (
                        cls_name, spiders.ids_max_retry_times))

                    sub_list_file = os.path.join(BASE_DIR,'cofcoAPP/heplers/journal',spiders.journal_year+"-"+cls_name+'.txt')
                    if os.path.exists(sub_list_file) and spiders.read_cached:
                        with open(sub_list_file,'r',encoding='utf-8') as f:
                            list_content = f.read()
                        sub_list = re.split('\n',list_content)[:-1]

                        for id_n,target_link in enumerate(sub_list):
                            self.ids_queen.put({'id_n': id_n, 'target_link': target_link, 'retry_times': 0})
                            self.manager.update_ids_qsize(1)
                        self.manager.update_finished_page_Num()
                        continue

                    currPage = 1
                    page_retried = 0
                    total_Num = 9999 #暂时的总期刊数目
                    curr_num = 0 # 目前通过翻页查询到的
                    is_get_last_journal = False # 是否获取到了最后一本期刊
                    while True and curr_num <= total_Num and not is_get_last_journal:
                        # 检查是否被暂停
                        if self.manager.idsP_status.value == 2:
                            time.sleep(1)  # 歇息一秒，继续检查
                            continue
                        # 检查是否任务是否完成
                        if self.manager.idsP_status.value == 3:
                            time.sleep(1)  # 歇息一秒，继续检查
                            continue
                        # 检查是否任务是否需要输入cookies
                        if self.manager.idsP_status.value == 6:
                            time.sleep(1)  # 歇息一秒，继续检查
                            continue

                        # 检查是否时被终止
                        if self.manager.idsP_status.value == 4:
                            break

                        if (page_retried >= spiders.ids_max_retry_times):
                            currPage += 1
                            continue
                        self.manager.idsP_status.value = 1
                        try:
                            real_pre = str(currPage-1)
                            # real_pre = '4'
                            real_curr = str(currPage)
                            if currPage == 1:
                                real_curr = ''
                                real_pre = '1'
                            self.data['ctl00$ContentPlaceHolder1$AspNetPager1_input'] = real_pre
                            self.data['__EVENTARGUMENT'] = real_curr
                            self.data['ctl00$ContentPlaceHolder1$dplCategory'] = cls_name

                            rsp = self.manager.ajax_sessionHelper.post('https://www.fenqubiao.com/Core/CategoryList.aspx',data=self.data)
                            if rsp.status_code != 200:
                                raise Exception('Connection Failed!')
                            rsp_text = rsp.text

                            # 寻找总期刊数目，同时也用于判断是否获取了正确的网页
                            re_r = re.search(r"期刊数量共计[\s\S]*?>([\d]+)[\s\S]*?本", rsp_text)
                            if not re_r:
                                raise Exception('Cant find the totalNum')
                            total_Num = int(re_r.group(1))

                            # 获取本页所有链接
                            row_eles = re.findall(r'<tr>\s+<td>([\d]+)</td>[\s\S]*?href="([\s\S]+?)"',rsp_text)
                            id_n = -1
                            fp = open(sub_list_file, 'a+', encoding='utf-8')
                            for ele in row_eles:
                                id_n = int(ele[0]) # 编号
                                target_link = ele[1] # 详情链接
                                self.ids_queen.put({'id_n': id_n, 'target_link':target_link, 'retry_times': 0})
                                fp.write(target_link+'\n')
                                self.manager.update_ids_qsize(1)
                                if int(id_n) == total_Num:
                                    is_get_last_journal = True
                            fp.flush()
                            fp.close()
                            logger.log(user=self.name, tag='INFO', info='%s-%d success! currPage:%d %d/%d' %(cls_name, currPage, currPage,id_n, total_Num), screen=True)
                            currPage += 1
                            page_retried = 0
                        except Exception as e:
                            page_retried += 1
                            logger.log(user=self.name, tag='ERROF', info='%s-%d failed! %s' % (cls_name, currPage, e), screen=True)
                            self.manager.auto_update_session(force=True)
                            self._init_data()
                    self.manager.update_finished_page_Num()

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
                            self.cls_queen.put(task_info)
                        else:  # 该任务确认已经失败，进行一些后续操作
                            self.manager.update_failed_page_Num()
                        logger.log(user=self.name, tag='ERROR', info=e, screen=True)
                        self.manager.auto_update_session(force=True)
                        self._init_data()
                    else:
                        pass
                        # logger.log(user=self.name, tag='INFO', info='Waiting...', screen=True)
                time.sleep(1.0 * random.randrange(1, 1000) / 1000)  # 休息一下

    def run(self):
        # 获取类别列表
        cls_names = ['地学','地学天文','工程技术','管理科学','化学','环境科学与生态学','农林科学','社会科学','生物','数学','物理','医学','综合性期刊']
        # cls_names = ['工程技术']
        SPIDERS_STATUS[self.kw_id].page_Num.value = len(cls_names)

        for cls_name in cls_names:
            self.cls_queen.put({'cls_name': cls_name,'retry_times':0})

        # for i in range(self.thread_num):
        for i in range(4):
            name = "%s %s-%02d" % (self.name, 'THREAD', i + 1)
            dt = self._worker(kw_id=self.kw_id, name=name, cls_queen=self.cls_queen)
            dt.start()
            self.threads.append(dt)

        # 合并到父进程
        for t in self.threads:
            t.join()

# 根据article_id爬取文章内容，每个进程有好几个线程
class _journalContendWorker(Process):
    def __init__(self, kw_id, name=None, thread_num=8):
        Process.__init__(self)
        self.kw_id = kw_id
        self.name = name
        self.thread_num = thread_num
        self.threads = []

    class _worker(threading.Thread):
        def __init__(self, kw_id, name=None, cookies=None):
            threading.Thread.__init__(self)
            self.name = name
            self.kw_id = kw_id
            self.sessionHelper = None
            self.cookies = cookies
            if kw_id:
                self.manager = SPIDERS_STATUS[kw_id]
                self.ids_queen = self.manager.ids_queen

        def run(self):
            self.manager.auto_update_session()
            while True:
                # 检查是否被暂停
                if self.manager.contentP_status.value == 2:  # 任务被暂停
                    time.sleep(1)  # 歇息一秒，继续检查
                    continue

                # 检查是否任务是否完成
                if self.manager.contentP_status.value == 3:
                    time.sleep(1)  # 歇息一秒，继续检查
                    continue

                # 检查是否任务是否需要输入cookies
                if self.manager.contentP_status.value == 6:
                    time.sleep(1)  # 歇息一秒，继续检查
                    continue

                # 检查是否时被终止
                if self.manager.contentP_status.value == 4:
                    break

                task_info = None
                try:
                    self.manager.contentP_status.value = 1
                    task_info = self.ids_queen.get(timeout=1)
                    id_n = str(task_info['id_n'])
                    target_link = str(task_info['target_link'])
                    retry_times = int(task_info['retry_times'])

                    if (retry_times >= spiders.content_max_retry_times):
                        raise Exception('%s: retry_times>=%d! This id is labeled as FAILED!'%(id_n, spiders.content_max_retry_times))

                    rsp = self.manager.page_sessionHelper.get('https://www.fenqubiao.com/Core/'+target_link)

                    if rsp.status_code != 200:
                        raise Exception('Connection Failed!')
                    rsp_text = rsp.text

                    r = re.search(r'点击按钮开始智能验证', rsp_text)
                    if r:
                        raise Exception('Logged in Failed! Please re-loggin!')
                    try:
                        journal_model = Journal()
                        journal_model.issn = re.search(r'ISSN[\s\S]*?valueCss">([\s\S]*?)</td>',rsp_text).group(1)
                        journal_model.full_name = re.search(r'期刊全称[\s\S]*?="3">([\s\S]*?)</td>',rsp_text).group(1)
                        journal_model.short_name = re.search(r'期刊简称[\s\S]*?valueCss">([\s\S]*?)</td>',rsp_text).group(1)
                        journal_model.subject = re.search(r'大类[\s\S]*?<td>([\s\S]*?)</td>',rsp_text).group(1)
                        journal_model.journal_zone = re.search(r'大类[\s\S]*?<td>[\s\S]*?center">\s+([\d]+)',rsp_text).group(1)
                        journal_model.impact_factor = re.findall(r'<td>([\d.]+)</td>',rsp_text)[3]
                        journal_model.is_survey = re.search(r'综述：[\s\S]*?valueCss">([\s\S]*?)</td>',rsp_text).group(1)
                        journal_model.is_top = re.search(r'大类[\s\S]*?top width-10[\s\S]*?ter">(\S+?)</td>',rsp_text).group(1)
                        journal_model.total_cited = re.findall(r'<td>([\d.]+)</td>',rsp_text)[6]
                        journal_model.save()
                    except Exception as e:
                        txt_path = os.path.join(BASE_DIR, 'test/faild_journal_details', target_link +'.txt')
                        with open(txt_path, 'w+', encoding='utf-8') as f:
                            f.write(rsp_text)
                        raise e

                    # =============================================================================================
                    self.manager.update_finish()
                    info = "%s/%s" % (self.manager.finished_num.value, self.manager.ids_queen_size.value)
                    logger.log(user=self.name, tag='INFO', info=info, screen=True)
                    time.sleep(1.0 * random.randrange(1, 1000) / 1000)  # 休息一下
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
                        self.manager.auto_update_session(force=True)
                        logger.log(user=self.name, tag='ERROR', info="%s" % (e), screen=True)
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
class SpiderManagerForJournal(object):

    # 比较特殊，只能放到init 外部
    kw_name = Manager().Value(c_char_p, '无')

    def __init__(self,ids_thread_num=4, content_process_num=2, content_thread_num=8, **kwargs):
        manager = Manager()
        # 爬虫的状态信息
        self.kw_id = spiders.journal_kw_id
        if SPIDERS_STATUS.get(self.kw_id):
            raise Exception('Journal spider is running!')
        self.TYPE = 'JOURNAL_SPIDER'
        self.id_process = None  # ID进程对象
        self.content_process = []  # Content进程对象
        self.ids_thread_num = ids_thread_num  # ids线程个数
        self.content_process_num = content_process_num  # Content进程个数
        self.content_thread_num = content_thread_num  # 每个Content进程的线程个数

        self.ids_queen = ProcessQueen(maxsize=-1)  # 待爬取的文章ID列表，是个队列
        self.ids_queen = ProcessQueen(maxsize=-1)  # 待爬取的文章ID列表，是个队列
        self.page_Num = Value('i', -1, lock=True)  # 页数
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
        self.page_sessionHelper = None
        self.ajax_sessionHelper = None
        self.journal_user_name = None
        self.journal_cookies = manager.dict() #存贮正在使用的cookie, 当为None时，表示正在等待用户输入cookie
        self.journal_cookies['main'] = None

        SPIDERS_STATUS[self.kw_id] = self

    def update_cookies(self,cookies):
        self.journal_cookies['main'] = cookies

    def auto_update_session(self, force=False):
        while True:
            try:
                # 检查cookie是否被设置
                if self.journal_cookies['main'] is None:
                    self.idsP_status.value = 6    # cookie无效, 等待重新输入
                    self.contentP_status.value = 6 # cookie无效, 等待重新输入
                    time.sleep(1)  # 歇息一秒，继续检查
                    raise Exception('Cookies are None or invalided. Please set it.')

                # 如果不是强制更新，则结束函数
                if self.ajax_sessionHelper and not force:
                    return

                # 表示未初始化或者要求强制更新
                # 检查helper是否被设置
                if self.page_sessionHelper is None:
                    self.page_sessionHelper = SessionHelper(header_fun=HeadersHelper.jounal_headers_page, try_proxy=False,
                                              cookies=self.journal_cookies['main'])
                # 检查cookie是否有效
                user_name = heplers.check_cookies_valid(self.page_sessionHelper)
                if not user_name: # 无效
                    self.journal_cookies['main'] = None   # 无效cookie置为空
                    self.page_sessionHelper = None # 无效cookie置为空
                    self.ajax_sessionHelper = None # 无效cookie置为空
                    self.kw_name = '<span style="color:red">无效cookies，请重新输入</span>' # 无效cookie置为空
                    raise Exception('This cookies cant be used to login.')

                self.page_sessionHelper = SessionHelper(header_fun=HeadersHelper.jounal_headers_page,
                                                        try_proxy=False,
                                                        cookies=self.journal_cookies['main'])
                self.ajax_sessionHelper = SessionHelper(header_fun=HeadersHelper.jounal_headers_ajax, try_proxy=False,
                                                   cookies=self.journal_cookies['main'])

                self.kw_name = '<span style="color:green">'+user_name+'</span>'
                logger.log(user=self.TYPE, tag='INFO', info='auto_update_session success!', screen=True)
                break
            except Exception as e:
                logger.log(tag="ERROR",user=self.TYPE, info='Check the cookies failed! ' + str(e), screen=True)
                time.sleep(1)
        logger.log(user=self.TYPE, tag='INFO', info='auto_update_session ended', screen=True)

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
        id_worker = _journalIDWorker(kw_id=self.kw_id, name='%s JOURNAL_IDS_PROCESS-MAIN' % common_tag, thread_num=self.ids_thread_num)
        id_worker.start()
        self.id_process = id_worker
        self.idsP_status.value = 1

        # 启动获取 content 的进程
        for i in range(self.content_process_num):
            name = '%s JOURNAL_CONTEND_PROCESS-%02d' % (common_tag, int(i + 1))
            content_worker = _journalContendWorker(kw_id=self.kw_id, name=name,thread_num=self.content_thread_num)
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
            if self.idsP_status.value != 2 and self.idsP_status.value != 6:
                error_.append(Exception('IDS process status is invalided'))
            else:
                self.idsP_status.value = 1
        if contentP:
            if self.contentP_status.value != 2 and self.contentP_status.value != 6:
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

    def __getattribute__(self,name):
        if name == 'kw_name':
            return object.__getattribute__(self, name).value
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, key, value):
        if key == 'kw_name':
            object.__getattribute__(self, key).value = value
        else:
            object.__setattr__(self,key,value)

if __name__ == '__main__':
    raw_cookies = '_uab_collina=155445267527536182817685; _umdata=GD8F42202B2EB11BCD37277697328EF9B09FBF7; ASP.NET_SessionId=wkadmyadz3ckvsmlhvieayth; Hm_lvt_0dae59e1f85da1153b28fb5a2671647f=1557330157,1557330220,1557330323,1557552986; __AntiXsrfToken=b72b2d5031cb48c8b0989e9c17efb202; Hm_lpvt_0dae59e1f85da1153b28fb5a2671647f=1557586795'
    sfp = SpiderManagerForJournal(create_user_id='uid', create_user_name='uname')
    sfp.journal_cookies = heplers.parse_raw_cookies(raw_cookies)
    sfp.start()

    print('start successful')


