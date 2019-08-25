from django.conf.urls import url, include
from django.contrib import admin

from books.views import MainPage


urlpatterns = [

    url(r'^$', MainPage.as_view(), name='mainpage'),  # 主页

]
