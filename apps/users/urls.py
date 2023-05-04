from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from users.views import user_list, user_edit

urlpatterns = [
    path('admin/', admin.site.urls, name="admin"),
    path('userList/', user_list, name="user_list"),
    path('useredit/<int:user_id>/', user_edit, name='user_edit'),
]
