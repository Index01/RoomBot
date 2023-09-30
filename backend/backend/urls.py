"""room_bot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, re_path
from reservations import views_flat

from reservations.views import guests
from reservations.views import rooms
from reservations.views import login



urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^api/guests/$', guests.guest_list),
    re_path(r'^api/guests/([0-9])$', guests.guest_detail),
    re_path(r'^api/rooms/$', rooms.room_list),
    re_path(r'^api/rooms/([0-9])$', rooms.room_detail),
    re_path(r'^api/login/$', login.login),
    re_path(r'^api/my_rooms/$', rooms.my_rooms),
    re_path(r'^api/swap_gen/$', rooms.swap_gen),
    re_path(r'^api/swap_it_up/$', rooms.swap_it_up),
    re_path(r'^api/swap_request/$', rooms.swap_request),
    re_path(r'^api/login_reset/$', login.login_reset),
]

 
