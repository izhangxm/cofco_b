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
import re
import random
from cofcoAPP import spiders
from cofcoAPP.spiders import logger


class ProxyHelper(object):
    def __init__(self, use_proxy=spiders.default_use_proxy, proxy_ips=spiders.default_proxy_ips_list,
                 proxy_pool_url=spiders.default_proxy_pool_url):
        self.use_proxy = use_proxy
        self.proxy_ips = proxy_ips
        self.proxy_pool_url = proxy_pool_url

    def get_proxy(self):
        if not self.use_proxy:
            return None
        while True:
            try:
                if self.proxy_ips and len(self.proxy_ips) > 0:
                    random.shuffle(self.proxy_ips)
                    ip = self.proxy_ips[0]
                elif self.proxy_pool_url and self.proxy_pool_url != '':
                    rsp = requests.get(self.proxy_pool_url)
                    if len(rsp.text) > 21:
                        raise Exception('Get Proxy Failed')
                    else:
                        ip = re.sub(r"\s", "", rsp.text)
                else:
                    return None
                proxies = {'http': 'http://' + ip, 'https': 'http://' + ip}
                return proxies
            except Exception as e:
                logger.log(user='ProxyHelper', tag='ERROR', info=e, screen=True)
                time.sleep(2)
