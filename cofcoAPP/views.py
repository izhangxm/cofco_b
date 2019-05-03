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
from django.shortcuts import render
from django.http import JsonResponse
from cofcoAPP.spiders import SPIDERS_STATUS
from cofcoAPP.spiders.PubmedSpider import SpiderManagerForPubmed
from cofcoAPP.spiders.ScienceDirectSpider import SpiderManagerForScience
from cofcoAPP.spiders import STATUS_NAME
from cofcoAPP import spiders
def index(request):
    context = {}
    context['title'] = '爬虫测试'
    return render(request, 'index.html', context)

def getStatus(request):
    resp_data = {'status': 1, "code": '200', "info": "ok", "data": []}
    resp_data['data'].append({'key':'爬虫总数', 'value':len(SPIDERS_STATUS.keys())})

    task_num = 0
    finished_num = 0
    for kw_id,spm in SPIDERS_STATUS.items():
        task_num +=spm.ids_queen_size.value
        finished_num += spm.finished_num.value
    resp_data['data'].append({'key': '任务总数', 'value': task_num})
    resp_data['data'].append({'key': '完成总数', 'value': finished_num})

    finish_rate = '--'
    if task_num >0:
        finish_rate = "%.1f%%" % (100.0 * finished_num / task_num)
    resp_data['data'].append({'key': '完成比例', 'value':finish_rate})
    return JsonResponse(resp_data)

#获取进程运行状态，返回值为json
def getThreadStatus(request):
    resp_data = {'status':1,"code": '200', "info": "ok"}
    resp_data['data'] = {}
    resp_data['data']['titles'] = ['uid','uname','kw_id','sp_t','w_num',
            'pN','f_pN','fail_pN',
            'f_num','fail_num','total_num',
            'idsP_status','cP_status',
            'c_time','s_time','status','operation']
    resp_data['data']['statusName'] = STATUS_NAME
    resp_data['data']['threadlist'] = []
    for kw_id,spm in SPIDERS_STATUS.items():
        worker_num =spm.content_process_num*spm.content_thread_num
        # spm = SpiderManagerForPubmed()
        data = {'uid':spm.create_user_id,'uname':spm.create_user_name,'kw_id':spm.kw_id,'sp_t':spm.TYPE,'w_num':worker_num,
                'pN':spm.page_Num.value, 'f_pN':spm.finished_page_Num.value, 'fail_pN':spm.failed_page_Num.value,
                'f_num':spm.finished_num.value, 'fail_num':spm.failed_num.value,'total_num': spm.ids_queen_size.value,
                'idsP_status':spm.idsP_status.value, 'cP_status':spm.contentP_status.value,
                'c_time':spm.create_time, 's_time':spm.start_time, 'status':spm.getStatus(),'operation': 'operation'
                }
        resp_data['data']['threadlist'].append(data)
    return JsonResponse(resp_data)

def get_format_content(request):
    resp_data = {'status': 1, "code": '200', "info": "ok"}
    try:
        pass

    except Exception as e:
        resp_data['status'] = 0
        resp_data['info'] = 'start failed: ' + str(e)
    return JsonResponse(resp_data)


def controlSpider(request):
    resp_data = {'status': 1, "code": '200', "info": "ok"}
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
            spider_type = request.POST.get('spider_type')
            uid = request.POST.get('uid')
            uname = request.POST.get('uname')

            ids_thread_num = int(request.POST.get('ids_thread_num', spiders.defalt_ids_thread_num))
            content_process_num = int(request.POST.get('content_process_num', spiders.defalt_content_process_num))
            content_thread_num = int(request.POST.get('content_thread_num', spiders.defalt_content_thread_num))

            if not kw_id or not uid or not uname:
                raise Exception('kw_id,uid and uname is required')
            if spider_type != '1' and spider_type != '2':
                raise Exception('spider_type is invalided')

            if spider_type == '1':
                sfp = SpiderManagerForPubmed(kw_id=kw_id,
                                             ids_thread_num=ids_thread_num,
                                             content_process_num=content_process_num,
                                             content_thread_num=content_thread_num,
                                             create_user_id=uid,
                                             create_user_name=uname)
                sfp.start()
            elif spider_type == '2':
                sfp = SpiderManagerForScience(kw_id=kw_id,
                                              ids_thread_num=ids_thread_num,
                                              content_process_num=content_process_num,
                                              content_thread_num=content_thread_num,
                                              create_user_id=uid,
                                              create_user_name=uname)
                sfp.start()

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
        for err in error_:
            raise Exception(err)
    except Exception as e:
        resp_data['status'] = 0
        resp_data['info'] = 'Failed: ' + str(e)
    return JsonResponse(resp_data)



