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
"""
IP代理池
随机Header
Session构造器
"""
import requests
from cofcoAPP.heplers.ProxyHelper import ProxyHelper
from cofcoAPP.heplers import  HeadersHelper
from cofcoAPP import spiders

# 自动随机session生成
class SessionHelper(object):
    def __init__(self, header_fun=None, try_proxy=True, cookies=None, verify=spiders.default_verify, timeout=spiders.default_timeout):
        self.proxyHelper = ProxyHelper()
        self.default_verify = verify
        self.default_timeout = timeout
        self.header_fun = header_fun
        self.try_proxy = try_proxy
        self.cookies = cookies # 标准格式的cookies
        self.lastQueryKey= None
        self.session = self.get_session()

    def get_session(self):
        session = requests.Session()
        proxies = None
        if self.try_proxy:
            proxies = self.proxyHelper.get_proxy()
        headers = None
        if self.header_fun:
            headers = self.header_fun()
        if headers:
            session.headers.update(headers)
        if proxies:
            session.proxies.update(proxies)
        if self.cookies:
            requests.utils.add_dict_to_cookiejar(session.cookies, self.cookies)
        return session

    def get(self,url, **kwargs):
        rsp = self.session.get(url, **kwargs, verify=self.default_verify, timeout=self.default_timeout)
        return rsp

    def post(self,url, **kwargs):
        rsp = self.session.post(url, **kwargs, verify=self.default_verify, timeout=self.default_timeout)
        return rsp



if __name__ == '__main__':
    sessionHelper = SessionHelper(header_fun=HeadersHelper.pubmed_ids_headers)
    rsp = sessionHelper.get('https://wwww.baidu.com')
    print(rsp.text)
    rsp = sessionHelper.post('https://wwww.baidu.com',data={})
    print(rsp.text)


