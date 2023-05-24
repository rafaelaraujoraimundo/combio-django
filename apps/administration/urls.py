from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from administration.views import user_list, user_edit

urlpatterns = [
    path('userList/', user_list, name="users"),
    path('useredit/<int:user_id>/', user_edit, name='user_edit'),
]
