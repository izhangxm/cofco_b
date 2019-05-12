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
from cofcoAPP.spiders.PubmedSpider import SpiderManagerForPubmed
from cofcoAPP.spiders.ScienceDirectSpider import SpiderManagerForScience
from cofcoAPP.spiders.JournalSpider import SpiderManagerForJournal
from cofcoAPP import spiders
from cofcoAPP.heplers import StatusHelper
from cofcoAPP import heplers


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
            raise Exception('kw_id is invalided')
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

                sfp = SpiderManagerForJournal(kw_id=spiders.journal_kw_id,
                                              ids_thread_num=ids_thread_num,
                                              content_process_num=content_process_num,
                                              content_thread_num=content_thread_num,
                                              create_user_id=uid,
                                              create_user_name=uname)
                sfp.update_cookies(heplers.parse_raw_cookies(raw_cookies))
                sfp.start()
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