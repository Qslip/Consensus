from django.urls import path, include
from .import views

urlpatterns = [
    path('', views.home, name='home'),
    path('index/', views.index, name='microblog_index'),
]
