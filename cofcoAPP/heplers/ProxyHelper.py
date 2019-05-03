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
import requests
import time
from cofcoAPP import spiders
class ProxyHelper(object):
    def __init__(self,use_proxy=spiders.default_use_proxy, proxy_ip=spiders.default_proxy_ip,proxy_pool_url=spiders.default_proxy_pool_url):
        self.use_proxy = use_proxy
        self.proxy_ip = proxy_ip
        self.proxy_pool_url = proxy_pool_url
    def get_proxy(self):
        if not self.use_proxy:
            return  None
        while True:
            try:
                ip = self.proxy_ip
                if not self.proxy_ip:
                    rsp = requests.get(self.proxy_pool_url)
                    ip = rsp.text
                proxies = {'http': 'http://' + ip, 'https': 'http://' + ip}
                return proxies
            except Exception as e:
                time.sleep(0.1)