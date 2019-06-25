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
from django.apps.registry import apps
from threading import Thread
import time
import re
import html
import json
from cofcoAPP import spiders
from cofcoAPP.spiders import logger
import asyncio
from . import close_old_connections

class AutoUpdateConfig(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.config = {}

    def waiting_for_app_ready(self):
        while not apps.apps_ready:
            time.sleep(0.1)

    def load_all_config(self):
        from cofcoAPP.models import AdminConfig
        close_old_connections()
        configs = AdminConfig.objects.filter(group='spider')
        for conf_obj in configs:
            key_name = conf_obj.name
            self.config[key_name] = conf_obj.value

    def get_config(self, key):
        return self.config.get(key)

    def set_spiders_value(self, key, type):
        value = self.get_config(key)
        if value is None or value == '':
            return
        if type == int:
            value = int(value)
        elif type == bool:
            value = bool(value)
        elif type == list:
            value = re.split(re.compile(r'\s+', re.I| re.M), value)
        elif type == dict:
            value = json.loads(html.unescape(value))
        elif type == str:
            value = str(value)
        setattr(spiders, key, value)

    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.waiting_for_app_ready() # 只有等到django准备好之后 才能导入相应的包
        time.sleep(3)
        while True:
            try:
                self.load_all_config()

                self.set_spiders_value('default_ids_thread_num',int)
                self.set_spiders_value('default_content_process_num', int)
                self.set_spiders_value('default_content_thread_num', int)

                self.set_spiders_value('ids_max_retry_times', int)
                self.set_spiders_value('content_max_retry_times', int)
                self.set_spiders_value('default_timeout', int)
                self.set_spiders_value('default_verify', bool)

                self.set_spiders_value('default_use_proxy', bool)
                self.set_spiders_value('default_proxy_ips_list', list)
                self.set_spiders_value('opt_headers',  dict)
                self.set_spiders_value('default_proxy_pool_url', str)

                logger.log(user='AutoUpdateConfig', tag='INFO', info='Spider configs have been updated automatically!', screen=True)
            except Exception as e:
                time.sleep(10)
                logger.log(user='AutoUpdateConfig', tag='ERROR', info=e, screen=True)
            time.sleep(3)


