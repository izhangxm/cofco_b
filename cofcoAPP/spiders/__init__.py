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
from multiprocessing import Lock
from cofco_b import settings
import os
from cofcoAPP.heplers import Logger

SPIDERS_STATUS = {} # 所有爬虫状态表

SCREEN_PRINT_LOCK = Lock() # 屏幕输出锁
LOG_FILE_LOCK = Lock()  # 日志写入锁
logfile = os.path.join(settings.BASE_DIR,'cofcoAPP','logs','spiderlog.txt')

logger = Logger(fp_locker=LOG_FILE_LOCK, file_path=logfile,screen_locker=SCREEN_PRINT_LOCK)
# 定义状态名称
STATUS_NAME = {-2:'失败', -1: '未初始化', 0: '未运行', 1: '运行中', 2: '已暂停', 3:'已完成', 4:'已终止', 5:'混合状态'}

ids_max_retry_times = 30
content_max_retry_times = 10
defalt_timeout = 2
default_verify = True

default_use_proxy=False
default_proxy_ip="127.0.0.1:1087"
default_proxy_pool_url="http://39.98.67.159:5555/random"
# proxy_proxy_pool_url="http://39.98.67.159:5010/get/"








