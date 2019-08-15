from django.conf.urls import url, include
from django.contrib import admin

from books.views import Mainpage


urlpatterns = [

    url(r'^$', Mainpage.as_view(), name='mainpage'),  # 主页

]
