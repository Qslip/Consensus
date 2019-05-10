from django.urls import path, include
from zhihu import views 

urlpatterns = [
    path('', views.data)
]
