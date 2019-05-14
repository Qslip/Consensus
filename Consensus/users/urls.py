from django.urls import path, include
from . import views

app_name = 'user'

urlpatterns = [
    path('register/', views.register_index, name='user_register'),
    path('login/', views.login_index, name='user_login'),
    path('logout/', views.logout_index, name='user_logout'),
]
