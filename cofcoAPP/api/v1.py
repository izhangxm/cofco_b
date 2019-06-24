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

from django.http import JsonResponse
from cofcoAPP.spiders import SPIDERS_STATUS
from cofcoAPP.spiders.PubmedSpider import SpiderManagerForPubmed,_pubmedContendWorker
from cofcoAPP.spiders.ScienceDirectSpider import SpiderManagerForScience,_scienceContendWorker
from cofcoAPP.spiders.JournalSpider import SpiderManagerForJournal
from cofcoAPP.heplers import StatusHelper,ContentHelper
from cofcoAPP import heplers
from channels.generic.websocket import AsyncWebsocketConsumer
from cofcoAPP import spiders
from collections import deque
from cofcoAPP.spiders import logfile
from cofcoAPP.models import get_json_model

#获取进程运行状态，返回值为json
def getThreadStatus(request):
    resp_data = {'status':1,"code": '0', "info": "ok"}
    g_name = request.POST.get('g_name', 'ALL')
    kw_id = request.POST.get('kw_id', 'ALL')
    data={}
    try:
        all_data = StatusHelper.getThreadStatus()
        if g_name == 'ALL' or g_name == '':
            data = all_data
        else:
            data[g_name] = all_data.get(g_name)
            if not data[g_name]:
                raise Exception('Unknown g_name. It must be titles，review，statusName，threadlist')
        if kw_id != 'ALL' and kw_id != '':
            threadlist = []
            for thread in data['threadlist']:
                if thread['kw_id'] == kw_id:
                    threadlist.append(thread)
            if len(threadlist) == 0:
                raise Exception('Unknown kw_id.')
            data['threadlist'] = threadlist
        resp_data['data'] = data
    except Exception as e:
        resp_data['status'] = 0
        resp_data['code'] = 25
        resp_data['info'] = 'Failed: ' + str(e)
    return JsonResponse(resp_data)

def controlSpider(request):
    resp_data = {'status': 1, "code": '0', "info": "ok"}
    try:
        action = request.POST.get('action')
        kw_id = request.POST.get('kw_id')
        spider_m = SPIDERS_STATUS.get(kw_id)
        if not spider_m and action != 'new':
            raise Exception('kw_id is invalided or process is not found')
        idsP = bool(int(request.POST.get('idsP',True)))
        contentP = bool(int(request.POST.get('contentP',True)))

        error_ = []
        if action == 'new':
            spider_type = int(request.POST.get('spider_type'))
            uid = request.POST.get('uid')
            uname = request.POST.get('uname')

            ids_thread_num = int(request.POST.get('ids_thread_num', spiders.default_ids_thread_num))
            content_process_num = int(request.POST.get('content_process_num', spiders.default_content_process_num))
            content_thread_num = int(request.POST.get('content_thread_num', spiders.default_content_thread_num))

            if not uid or not uname:
                raise Exception('uid and uname is required')
            if spider_type != 3 and (not kw_id):
                raise Exception('kw_id is required')

            if spider_type == 1:
                sfp = SpiderManagerForPubmed(kw_id=kw_id,
                                             ids_thread_num=ids_thread_num,
                                             content_process_num=content_process_num,
                                             content_thread_num=content_thread_num,
                                             create_user_id=uid,
                                             create_user_name=uname)
                sfp.start()
            elif spider_type == 2:
                sfp = SpiderManagerForScience(kw_id=kw_id,
                                              ids_thread_num=ids_thread_num,
                                              content_process_num=content_process_num,
                                              content_thread_num=content_thread_num,
                                              create_user_id=uid,
                                              create_user_name=uname)
                sfp.start()
            elif spider_type == 3:
                raw_cookies = request.POST.get('raw_cookies')
                if not raw_cookies:
                    raise Exception('raw_cookies is required')

                try:
                    sfp = SpiderManagerForJournal(kw_id=spiders.journal_kw_id,
                                                  ids_thread_num=ids_thread_num,
                                                  content_process_num=content_process_num,
                                                  content_thread_num=content_thread_num,
                                                  create_user_id=uid,
                                                  create_user_name=uname)
                    sfp.update_cookies(heplers.parse_raw_cookies(raw_cookies))
                    sfp.start()
                except Exception as e:
                    spider_m = SPIDERS_STATUS.get(spiders.journal_kw_id)
                    if spider_m:
                        SPIDERS_STATUS.pop(spiders.journal_kw_id, None)
                    raise e
            else:
                raise Exception('Unknown spider type. It must be 1 or 2.')

            resp_data['info'] = 'start successful'
        elif action == 'pause':
            error_ = spider_m.pause(idsP=idsP,contentP=contentP)
            resp_data['info'] = 'pause successful'
        elif action == 'resume':
            error_ = spider_m.resume(idsP=idsP,contentP=contentP)
            resp_data['info'] = 'resume successful'
        elif action == 'terminate':
            error_ = spider_m.terminate(idsP=idsP,contentP=contentP)
            resp_data['info'] = 'terminate successful'
        elif action == 'del':
            error_ = spider_m.delete()
            resp_data['info'] = 'del successful'
        elif action == 'retry':
            spider_m.retry()

        else:
            raise Exception('unknown action')
        # for err in error_:
        #     raise Exception(err)
    except Exception as e:
        resp_data['status'] = 0
        resp_data['code'] = 25
        resp_data['info'] = 'Failed: ' + str(e)
    return JsonResponse(resp_data)


def update_cookies(request):
    resp_data = {'status': 1, "code": '0', "info": "ok"}
    try:
        raw_cookies = request.POST.get('raw_cookies', None)
        if raw_cookies is None:
            raise Exception('raw_cookies is None')
        if not SPIDERS_STATUS.get(spiders.journal_kw_id):
            raise Exception('Journal spider is not running!')

        SPIDERS_STATUS.get(spiders.journal_kw_id).update_cookies(heplers.parse_raw_cookies(raw_cookies))
        SPIDERS_STATUS.get(spiders.journal_kw_id).resume()

        resp_data['info'] = 'Update cookies successful'
    except Exception as e:
        resp_data['status'] = 0
        resp_data['code'] = 25
        resp_data['info'] = 'Failed: ' + str(e)
    return JsonResponse(resp_data)


def assist(request):
    resp_data = {'status': 1, "code": '0', "info": "ok"}
    try:
        urls = request.POST.get('urls', None)
        if urls is None:
            raise Exception('urls is None')
        urls = urls.replace(' ', '').split('\n')
        if len(urls) == 1:
            url_type = heplers.url_type(urls[0])
            if url_type == 'pubmed':
                worker = _pubmedContendWorker._worker(kw_id=None)
            elif url_type == 'sciencedirect':
                worker = _scienceContendWorker._worker(kw_id=None)
            else:
                raise Exception('Invalided url. Please read the tips on this page!')
            data_dict = worker.get_dict_data_from_link(urls[0])
            resp_data['data'] = data_dict
        else:
            pubmed_urls = []
            science_urls = []
            for url in urls:
                url_type = heplers.url_type(url)
                if url_type == 'pubmed':
                    pubmed_urls.append(url)
                elif url_type == 'sciencedirect':
                    science_urls.append(url)

        resp_data['info'] = 'ok'

    except Exception as e:
        resp_data['status'] = 0
        resp_data['code'] = 25
        resp_data['info'] = 'Failed: ' + str(e)
    return JsonResponse(resp_data)

# 检查用户的url是否合法
def check_urls(request):
    resp_data = {'status': 1, "code": '0', "info": "ok"}
    try:
        urls = request.POST.get('urls', None)
        if urls is None:
            raise Exception('urls is None')
        urls = urls.replace(' ', '').split('\n')

        # 利用set集合对url自动去重
        urls = set(urls)

        pubmed_urls = []
        science_urls = []
        invalided_urls = []


        for url in urls:
            if len(url)==0:
                continue
            url_type, reason = heplers.check_url(url)
            if reason:
                invalided_urls.append([url, reason])
            elif url_type == 'pubmed':
                pubmed_urls.append(url)
            elif url_type == 'sciencedirect':
                science_urls.append(url)

        info = 'Pubmed urls: %d<br/>' % len(pubmed_urls)
        info += 'ScienceDirect urls: %d<br/>' % len(science_urls)
        info += 'Invalided urls: %d<br/>' % len(invalided_urls)
        if len(invalided_urls) > 0:
            info += 'Invalided urls are listed as follows, please check and confirm their format.<br/>'
            in_valided_url_string = ""
            for index, inva_url in enumerate(invalided_urls):
                in_valided_url_string += '%d/%d. %s[<span style="color:red">%s</span>]<br/>' % (index+1,len(invalided_urls), inva_url[0],inva_url[1])
            info += in_valided_url_string
        resp_data['info'] = info

    except Exception as e:
        resp_data['status'] = 0
        resp_data['code'] = 25
        resp_data['info'] = 'Failed: ' + str(e)
    return JsonResponse(resp_data)


class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = spiders.group_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        spiders.connected.value = True
        logFile = open(logfile, 'r', encoding='utf-8')
        output = deque(logFile, 32)
        list1 = list(output)
        for item in list1:
            item = item.replace('\n', '')
            type_ = item.split(' ')[2]
            output_str = "\033[0;31m%s\033[0m" % (item)
            if type_ == 'INFO':
                output_str = '\033[0;32m%s\033[0m' % (item)
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'log_message',
                    'message': output_str
                }
            )
        logFile.close()
        await self.channel_layer.group_send( self.room_group_name, { 'type': 'log_message', 'message': "以上为历史消息....\n" })

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        spiders.connected.value = False

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        message = text_data

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'log_message',
                'message': message
            }
        )

    # Receive message from room group
    async def log_message(self, event):
        message = event['message']
        # Send message to WebSocket
        await self.send(text_data=message)