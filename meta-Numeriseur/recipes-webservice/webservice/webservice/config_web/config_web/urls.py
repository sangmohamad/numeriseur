"""config_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
#from django.urls import path, include # new
from django.views.generic.base import TemplateView # new

from home import views



urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url('accounts/', include('django.contrib.auth.urls')),
    url('Home', views.home, name='home'),
    url('Configuration', views.config, name='Config'),
    url(r'^user_login/$',views.user_login,name='user_login'),
    url(r'^logout/$', views.user_logout, name='logout'),
    #path('', TemplateView.as_view(template_name='home/home.html'), name='home'),
    url('debug_mic', views.mic_debug, name='mic'),
    url('debug_cab', views.cab_debug, name='cab'),
    url('audio_cab_record', views.audio_cab_record, name='audio_cab_record'),
    url('audio_mic_record', views.audio_mic_record, name='audio_mic_record'),
    url('mic_record', views.mic_record, name='mic_record'),
    url('install_mic', views.install_mic, name='install_mic'),
    url('record', views.record, name='record'),

    
    
]
