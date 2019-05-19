"""cofco_b URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from cofcoAPP import views
from cofcoAPP.api import v1

urlpatterns = [
    url(r'^$', views.index),
    url(r'^api/v1/getthreadstatus/$', v1.getThreadStatus),
    url(r'^api/v1/controlspider/$', v1.controlSpider),
    url(r'^api/v1/updatecookies/$', v1.update_cookies),
]

websocket_urlpatterns = [ # 路由，指定 websocket 链接对应的 consumer
    path('api/v1/viewlog/', v1.LogConsumer),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns )
    ),
})