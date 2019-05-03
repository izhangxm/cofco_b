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
from cofcoAPP.spiders import SPIDERS_STATUS
from cofcoAPP.spiders import STATUS_NAME

# 获取进程运行状态，返回值为json
def getThreadStatus():
    result = {}
    review = []
    review.append({'key': '爬虫总数', 'value': len(SPIDERS_STATUS.keys())})
    task_num = 0
    finished_num = 0
    for kw_id, spm in SPIDERS_STATUS.items():
        task_num += spm.ids_queen_size.value
        finished_num += spm.finished_num.value
    review.append({'key': '任务总数', 'value': task_num})
    review.append({'key': '完成总数', 'value': finished_num})
    finish_rate = '--'
    if task_num > 0:
        finish_rate = "%.1f%%" % (100.0 * finished_num / task_num)
    review.append({'key': '完成比例', 'value': finish_rate})
    result['review'] = review

    result['titles'] = {'uid': '用户ID', 'uname': '用户名', 'kw_id': '关键词ID', 'sp_t': '爬虫', 'w_num': '爬虫数目',
                                   'pN': '页数', 'f_pN': '完成页数', 'fail_pN': '失败页数',
                                   'f_num': '完成文章', 'fail_num': '失败文章', 'total_num': '总文章',
                                   'idsP_status': '翻页进程', 'cP_status': '文章获取进程',
                                   'c_time': '创建时间', 's_time': '最后启动时间', 'status': '总状态', 'operation': '操作'}
    result['statusName'] = STATUS_NAME
    result['threadlist'] = []
    for kw_id, spm in SPIDERS_STATUS.items():
        worker_num = spm.content_process_num * spm.content_thread_num
        # spm = SpiderManagerForPubmed()
        data = {'uid': spm.create_user_id, 'uname': spm.create_user_name, 'kw_id': spm.kw_id, 'sp_t': spm.TYPE,
                'w_num': worker_num,
                'pN': spm.page_Num.value, 'f_pN': spm.finished_page_Num.value, 'fail_pN': spm.failed_page_Num.value,
                'f_num': spm.finished_num.value, 'fail_num': spm.failed_num.value,
                'total_num': spm.ids_queen_size.value,
                'idsP_status': spm.idsP_status.value, 'cP_status': spm.contentP_status.value,
                'c_time': spm.create_time, 's_time': spm.start_time, 'status': spm.getStatus(), 'operation': 'operation'
                }
        result['threadlist'].append(data)
    return result
